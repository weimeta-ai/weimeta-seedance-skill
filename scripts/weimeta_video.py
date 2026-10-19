#!/usr/bin/env python3
"""WEIMETA Seedance Agent Skill. Python 3.9+, standard library only."""
import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.weimeta.cn/volcengine/v1"
DEFAULT_MODEL = "doubao-seedance-2-5-260628"
MODES = ("t2v", "i2v", "r2v", "edit", "extend")
IMAGE_MIME = {".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"}
AUDIO_MIME = {".wav":"audio/wav",".mp3":"audio/mpeg"}
TERMINAL = {"succeeded", "failed", "cancelled", "canceled", "expired"}

class SkillError(Exception):
    pass

def redact_output(obj):
    """Hide temporary media URLs and other credential-bearing fields in logs."""
    if isinstance(obj, list):
        return [redact_output(v) for v in obj]
    if isinstance(obj, dict):
        output = {}
        for k, v in obj.items():
            key = str(k).lower()
            if key in ("authorization", "api_key", "access_token", "secret_key"):
                output[k] = "[REDACTED]"
            elif key in ("video_url", "audio_url", "image_url") and isinstance(v, str):
                output[k] = "[MEDIA_URL_REDACTED]"
            else:
                output[k] = redact_output(v)
        return output
    if isinstance(obj, str):
        if obj.startswith("data:"):
            return "[INLINE_MEDIA_REDACTED]"
        if obj.startswith(("https://", "http://")) and urllib.parse.urlsplit(obj).query:
            return "[SIGNED_OR_PARAMETERIZED_URL_REDACTED]"
    return obj

def emit(obj):
    print(json.dumps(redact_output(obj), indent=2, ensure_ascii=False))

def endpoint():
    value = os.environ.get("WEIMETA_VIDEO_BASE_URL", DEFAULT_BASE).rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise SkillError("WEIMETA_VIDEO_BASE_URL must be an HTTPS API URL")
    return value

def credentials_file():
    return Path.home() / ".config" / "weimeta" / "seedance-credentials.json"

def secret():
    value = os.environ.get("WEIMETA_API_KEY", "").strip()
    if value:
        return value
    path = credentials_file()
    if path.is_file():
        try:
            if path.stat().st_mode & 0o077:
                raise SkillError("Credential file permissions must be 0600")
            data = json.loads(path.read_text(encoding="utf-8"))
            value = str(data.get("api_key", "")).strip()
            if value:
                return value
        except (ValueError, OSError) as e:
            raise SkillError("Cannot read credential file: " + str(e))
    raise SkillError("No API Key configured. Run 'configure' interactively in your own terminal.")

def configure():
    if not sys.stdin.isatty():
        raise SkillError("configure requires an interactive terminal")
    key = getpass.getpass("WEIMETA API Key (input hidden): ").strip()
    if not key:
        raise SkillError("Empty API Key rejected")
    path = credentials_file()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    import tempfile
    fd, temporary = tempfile.mkstemp(prefix=".seedance-", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"api_key": key}, stream)
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    emit({"configured": True, "credential_file": str(path), "key_value_displayed": False})


def media(value, kind):
    if value.startswith(("https://", "asset://")):
        return value
    if value.startswith("http://"):
        raise SkillError("HTTP media URLs are blocked; use HTTPS")
    f = Path(value).expanduser()
    if not f.is_file():
        raise SkillError("Media not found: " + value)
    if kind == "video":
        raise SkillError("Local video upload not supported; supply HTTPS or asset:// media reference")
    allowed = IMAGE_MIME if kind == "image" else AUDIO_MIME
    mime = allowed.get(f.suffix.lower())
    if not mime or f.stat().st_size > 10*1024*1024:
        raise SkillError("Unsupported media extension or file larger than 10MB: " + str(f))
    return "data:{};base64,{}".format(mime, base64.b64encode(f.read_bytes()).decode("ascii"))

def item(kind, value, role):
    field = kind + "_url"
    return {"type":field, field:{"url":media(value,kind)}, "role":role}

def payload(a):
    model = a.model or os.environ.get("WEIMETA_SEEDANCE_MODEL", DEFAULT_MODEL)
    pictures, videos, audio = a.image or [], a.video or [], a.audio or []
    first, last = a.first_frame, a.last_frame
    mode = a.mode
    if not model.strip():
        raise SkillError("Model ID is required")
    if not a.prompt and mode == "t2v":
        raise SkillError("Text-to-video requires --prompt")
    if mode == "t2v" and (first or last or pictures or videos or audio):
        raise SkillError("Text-to-video cannot include media; choose another mode")
    if mode == "i2v" and (not first or pictures or videos or audio):
        raise SkillError("Image-to-video requires --first-frame and no reference media")
    if last and not first:
        raise SkillError("--last-frame requires --first-frame")
    if mode in ("r2v","edit","extend") and (first or last):
        raise SkillError("Reference/edit/extend use --image/--video/--audio")
    if mode == "r2v" and not (pictures or videos or audio):
        raise SkillError("Reference mode requires at least one media input")
    if mode in ("edit","extend") and not videos:
        raise SkillError("Video edit/extend requires --video HTTPS or asset:// reference")
    if mode in ("edit","extend") and "seedance-2-5" not in model:
        raise SkillError("This version only supports video edit/extend on Seedance 2.5")
    if len(pictures)>30 or len(videos)>10 or len(audio)>10:
        raise SkillError("Too many reference inputs for this Skill")
    if a.duration is not None:
        if mode == "edit":
            if a.duration != -1: raise SkillError("Edit mode duration must be -1")
        elif "seedance-2-5" in model and not 4<=a.duration<=30: raise SkillError("Seedance 2.5 duration must be 4..30 seconds (unless edit)")
        elif "seedance-2-0" in model and not 4<=a.duration<=15: raise SkillError("Seedance 2.0 duration must be 4..15 seconds (unless edit)")
        elif "seedance-2-5" not in model and "seedance-2-0" not in model and not 2<=a.duration<=30: raise SkillError("Duration must be 2..30 seconds for custom model")
    if "seedance-2-5" in model and mode in ("i2v","edit","extend") and a.ratio not in (None,"adaptive"):
        raise SkillError("Seedance 2.5 image/edit/extend requires ratio=adaptive")
    content = []
    if a.prompt: content.append({"type":"text","text":a.prompt})
    if first: content.append(item("image", first, "first_frame"))
    if last: content.append(item("image", last, "last_frame"))
    for x in pictures: content.append(item("image", x, "reference_image"))
    for x in videos: content.append(item("video", x, "reference_video"))
    for x in audio: content.append(item("audio", x, "reference_audio"))
    body = {"model":model, "content":content, "resolution":a.resolution}
    if a.ratio: body["ratio"]=a.ratio
    if a.duration is not None: body["duration"]=a.duration
    if mode == "edit": body.update(duration=-1, ratio="adaptive")
    if mode == "extend": body["ratio"]="adaptive"
    if "seedance-2-5" in model and mode in ("r2v","edit","extend"):
        body["omni_reference_task_type"]={"r2v":"reference","edit":"edit","extend":"extend"}[mode]
    if a.generate_audio is not None: body["generate_audio"]=a.generate_audio
    if a.watermark is not None: body["watermark"]=a.watermark
    return body

def preview(body):
    result=json.loads(json.dumps(body))
    for part in result.get("content", []):
        for field in ("image_url","video_url","audio_url"):
            ref=part.get(field)
            if isinstance(ref,dict) and str(ref.get("url","")).startswith("data:"):
                ref["url"]="[LOCAL BASE64 MEDIA REDACTED]"
    return result

def request(method, path, data=None):
    url = endpoint()+"/"+path.lstrip("/")
    headers={"Authorization":"Bearer "+secret(),"Accept":"application/json",
             "User-Agent":"weimeta-seedance-skill/0.3.0"}
    body=None
    if data is not None:
        headers["Content-Type"]="application/json"
        body=json.dumps(data,ensure_ascii=False).encode("utf-8")
    req=urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            obj=json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg=e.read(1200).decode("utf-8",errors="replace").replace(secret(),"[REDACTED]")
        raise SkillError("Gateway HTTP {}: {}".format(e.code,msg))
    except (urllib.error.URLError,TimeoutError) as e:
        raise SkillError("API connection error. After POST, check platform logs before retrying: "+str(e))
    if not isinstance(obj,dict):
        raise SkillError("Gateway returned non-object JSON")
    return obj

def catalog():
    """Read-only list of models allowed for this API Key."""
    base = endpoint()
    origin = urllib.parse.urlsplit(base)
    url = urllib.parse.urlunsplit((origin.scheme, origin.netloc, "/v1/models", "", ""))
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + secret(), "Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SkillError("Model catalog HTTP " + str(e.code))
    except (urllib.error.URLError, TimeoutError) as e:
        raise SkillError("Model catalog connection error: " + str(e))
    items = result.get("data", []) if isinstance(result, dict) else []
    ids = sorted(set(x["id"] for x in items if isinstance(x, dict) and isinstance(x.get("id"), str) and "seedance" in x["id"].lower()))
    return {"model_catalog": url, "seedance_model_ids": ids, "catalog_checked": True, "fee_information_included": False}

def task(aid):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,180}",aid):
        raise SkillError("Invalid task ID")
    return request("GET","contents/generations/tasks/"+aid)

def outputdir(value):
    p=Path(value).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p

def save_task(obj, dirname):
    aid=obj.get("id")
    if not isinstance(aid,str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,180}",aid):
        raise SkillError("Task was submitted but response lacks a recognized task ID; check platform task list before retrying")
    path=outputdir(dirname)/("task-"+aid+".json")
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    path.chmod(0o600)
    return aid,path

def download(obj,dirname):
    data=obj.get("content")
    url=data.get("video_url") if isinstance(data,dict) else None
    if isinstance(url,dict): url=url.get("url")
    if not isinstance(url,str) or urllib.parse.urlsplit(url).scheme!="https":
        raise SkillError("Task has no valid HTTPS video_url")
    aid=obj.get("id","result")
    if not isinstance(aid,str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,180}",aid): aid="result"
    ext=Path(urllib.parse.urlsplit(url).path).suffix.lower()
    if ext not in (".mp4",".mov"): ext=".mp4"
    final=outputdir(dirname)/("weimeta-"+aid+ext)
    tmp=final.with_suffix(final.suffix+".part")
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"weimeta-seedance-skill/0.3.0"}),timeout=120) as r, tmp.open("wb") as f:
            while True:
                chunk=r.read(512*1024)
                if not chunk: break
                f.write(chunk)
        if tmp.stat().st_size == 0: raise SkillError("Downloaded video is empty")
        tmp.replace(final)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return str(final)

def poll(aid,timeout,interval,dirname,should_download):
    if timeout<5 or interval<3: raise SkillError("timeout >= 5 and interval >= 3 required")
    expiry=time.monotonic()+timeout
    while True:
        obj=task(aid)
        status=str(obj.get("status","unknown")).lower()
        print("task={} status={}".format(aid,status),file=sys.stderr)
        if status in TERMINAL:
            emit(obj)
            if status=="succeeded" and should_download:
                emit({"video_path":download(obj,dirname)})
            return 0 if status=="succeeded" else 2
        if time.monotonic()+interval>=expiry:
            print("Polling timed out. Keep task ID; do not submit again.",file=sys.stderr)
            return 3
        time.sleep(interval)

def parser():
    p=argparse.ArgumentParser(description="WEIMETA Seedance cross-Agent video CLI")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor",help="Offline environment check: no network, no billing")
    sub.add_parser("configure",help="Store API Key in 0600 local credential file through hidden terminal input")
    sub.add_parser("models",help="Query allowed Seedance model IDs (read-only, no video charge)")
    g=sub.add_parser("generate")
    g.add_argument("--prompt",default="")
    g.add_argument("--model")
    g.add_argument("--mode",choices=MODES,default="t2v")
    g.add_argument("--first-frame")
    g.add_argument("--last-frame")
    g.add_argument("--image",action="append")
    g.add_argument("--video",action="append")
    g.add_argument("--audio",action="append")
    g.add_argument("--resolution",choices=["480p","720p","1080p","4k"],default="720p")
    g.add_argument("--ratio",choices=["adaptive","16:9","9:16","1:1","4:3","3:4","21:9"])
    g.add_argument("--duration",type=int)
    g.add_argument("--generate-audio",dest="generate_audio",action="store_true")
    g.add_argument("--no-audio",dest="generate_audio",action="store_false")
    g.add_argument("--watermark",dest="watermark",action="store_true")
    g.add_argument("--no-watermark",dest="watermark",action="store_false")
    g.set_defaults(generate_audio=None,watermark=None)
    g.add_argument("--dry-run",action="store_true")
    g.add_argument("--confirm-charge",action="store_true")
    g.add_argument("--wait",action="store_true")
    g.add_argument("--timeout",type=int,default=900)
    g.add_argument("--interval",type=int,default=10)
    g.add_argument("--output-dir",default="~/Downloads/WEIMETA")
    t=sub.add_parser("task")
    t.add_argument("--task-id",required=True)
    t.add_argument("--wait",action="store_true")
    t.add_argument("--download",action="store_true")
    t.add_argument("--timeout",type=int,default=900)
    t.add_argument("--interval",type=int,default=10)
    t.add_argument("--output-dir",default="~/Downloads/WEIMETA")
    return p

def main(argv=None):
    a=parser().parse_args(argv)
    try:
        if a.command=="doctor":
            configured = bool(os.environ.get("WEIMETA_API_KEY", "").strip()) or credentials_file().is_file()
            emit({"skill":"weimeta-seedance","python":sys.version.split()[0],
                  "base_url":endpoint(),"model":os.environ.get("WEIMETA_SEEDANCE_MODEL",DEFAULT_MODEL),
                  "api_key_configured":configured,
                  "offline":True,"generation_charge":False})
            return 0
        if a.command=="configure":
            configure()
            return 0
        if a.command=="models":
            emit(catalog())
            return 0
        if a.command=="generate":
            data=payload(a)
            if a.dry_run:
                emit({"dry_run":True,"submits_task":False,"endpoint":endpoint()+"/contents/generations/tasks",
                      "request":preview(data),"pricing_verified":False})
                return 0
            if not a.confirm_charge:
                raise SkillError("Paid task submission blocked. Review account pricing and explicitly use --confirm-charge")
            resp=request("POST","contents/generations/tasks",data)
            aid,path=save_task(resp,a.output_dir)
            emit({"task_id":aid,"receipt":str(path),"billable":True})
            if a.wait:
                return poll(aid,a.timeout,a.interval,a.output_dir,True)
            return 0
        if a.wait:
            return poll(a.task_id,a.timeout,a.interval,a.output_dir,a.download)
        obj=task(a.task_id)
        emit(obj)
        if a.download and obj.get("status")=="succeeded":
            emit({"video_path":download(obj,a.output_dir)})
        return 0
    except (SkillError, OSError, ValueError, json.JSONDecodeError) as e:
        print("ERROR: "+str(e),file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())

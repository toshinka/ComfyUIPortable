import urllib.request, json, time, uuid, os

def run_job_a():
    print("=== STARTING JOB A: GUIDE / CONTROLNET ===")
    
    # 1. Fetch live capabilities
    caps_url = "http://127.0.0.1:8191/api/manga/generation/capabilities"
    with urllib.request.urlopen(caps_url) as r:
        caps = json.loads(r.read().decode())
    revision = caps["revision"]
    print(f"Live capability revision: {revision}")
    
    # Check queue before submission
    q_url = "http://127.0.0.1:8189/queue"
    with urllib.request.urlopen(q_url) as r:
        q = json.loads(r.read().decode())
    print(f"Pre-job queue: {len(q['queue_running'])} running, {len(q['queue_pending'])} pending")
    if len(q['queue_running']) > 0 or len(q['queue_pending']) > 0:
        raise RuntimeError("Queue is not empty! Foreign job in progress.")
        
    doc = {
        'schema_id': 'TEGAKI_AUTHORING_DOCUMENT',
        'schema_version': '1.0.0',
        'pages': [{
            'page_id': 'page_disposable_guide_test',
            'width_px': 832,
            'height_px': 1216,
            'style_prompt': 'simple illustration, distinct regions',
            'style_negative_prompt': '',
            'scenes': [{
                'scene_id': 'scene_left',
                'order': 1,
                'input_mode': 'simple',
                'prompt': 'red sports car',
                'negative_prompt': '',
                'area': {'shape_type': 'rect', 'x': 0.0, 'y': 0.0, 'w': 0.5, 'h': 1.0}
            }, {
                'scene_id': 'scene_right',
                'order': 2,
                'input_mode': 'simple',
                'prompt': 'blue ocean, open sea, horizon',
                'negative_prompt': '',
                'area': {'shape_type': 'rect', 'x': 0.5, 'y': 0.0, 'w': 0.5, 'h': 1.0}
            }],
            'guides': [{
                'guide_id': 'guide_1',
                'guide_type': 'rough_manga',
                'enabled': True,
                'asset_reference': 'tegaki_manga_guides/disposable_guide_car_ocean.png',
                'placement': {
                    'x': 0.0,
                    'y': 0.0,
                    'w': 1.0,
                    'h': 1.0,
                    'scale_x': 1.0,
                    'scale_y': 1.0
                },
                'figure_regions': [],
                'metadata': {
                    'fit_mode': 'contain',
                    'source_dimensions': {
                        'width_px': 832,
                        'height_px': 1216
                    }
                }
            }],
            'cast': [],
            'character_instances': [],
            'visual_frames': []
        }],
        'metadata': {}
    }

    settings = {
        'mode': 'scene',
        'checkpoint_id': '!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors',
        'authoring_document': doc,
        'page_index': 0,
        'sampler_id': 'euler',
        'scheduler_id': 'normal',
        'steps': 24,
        'cfg': 5.0,
        'seed_requested': '240924',
        'capability_revision': revision,
        'mask_feather': 16,
        'panel_strength': 1.0,
        'controlnet_strength': 0.35
    }
    
    # 2. Compile Scene
    req_id = str(uuid.uuid4())
    compile_req = urllib.request.Request(
        'http://127.0.0.1:8191/api/manga/generation/compile-scene',
        data=json.dumps({**settings, 'request_id': req_id}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(compile_req) as r:
        compiled = json.loads(r.read().decode())
    
    print(f"Compile successful. Graph digest: {compiled['graph_digest']}")
    print(f"Audit trail: {json.dumps(compiled.get('audit_trail', {}), indent=2)}")
    
    # 3. Create Manga Job (submits exactly ONE job to GPU)
    idempotency_key = str(uuid.uuid4())
    job_payload = {
        'settings': settings,
        'idempotency_key': idempotency_key,
        'expected_graph_digest': compiled['graph_digest']
    }
    
    job_req = urllib.request.Request(
        'http://127.0.0.1:8191/api/manga/generation/jobs',
        data=json.dumps(job_payload).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(job_req) as r:
        job_data = json.loads(r.read().decode())
    
    job = job_data['job']
    job_id = job['job_id']
    print(f"Job created: {job_id}, Initial State: {job['state']}")
    
    # 4. Poll job status until completion
    start_time = time.time()
    last_state = job['state']
    while True:
        time.sleep(2)
        elapsed = time.time() - start_time
        poll_req = urllib.request.Request(f"http://127.0.0.1:8191/api/manga/generation/jobs/{job_id}")
        with urllib.request.urlopen(poll_req) as r:
            cur = json.loads(r.read().decode())['job']
        
        state = cur['state']
        if state != last_state:
            print(f"[{elapsed:.1f}s] State transition: {last_state} -> {state}")
            last_state = state
            
        if state == "SUCCEEDED":
            print(f"[{elapsed:.1f}s] Job SUCCEEDED!")
            print(f"Output locator: {cur.get('output_locator')}")
            print(f"Prompt ID: {cur.get('prompt_id')}")
            break
        elif state in ("FAILED", "UNKNOWN"):
            print(f"[{elapsed:.1f}s] Job ended in {state}: {cur.get('error')}")
            raise RuntimeError(f"Job failed: {cur.get('error')}")
        elif elapsed > 300: # 5 min timeout
            raise TimeoutError("Job execution timed out after 300 seconds")
            
    # 5. Fetch verified result image
    res_url = f"http://127.0.0.1:8191/api/manga/generation/jobs/{job_id}/result"
    with urllib.request.urlopen(res_url) as r:
        img_bytes = r.read()
    
    os.makedirs("scratch", exist_ok=True)
    out_path = os.path.join("scratch", "job_a_guide_result.png")
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    print(f"Result image saved to {out_path} ({len(img_bytes)} bytes)")
    
    # Save job record metadata
    meta_path = os.path.join("scratch", "job_a_guide_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            'job': cur,
            'compiled': compiled,
            'settings': settings,
            'execution_time_seconds': round(elapsed, 2)
        }, f, indent=2)
    print(f"Metadata saved to {meta_path}")

if __name__ == "__main__":
    run_job_a()

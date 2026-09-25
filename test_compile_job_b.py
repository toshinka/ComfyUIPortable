import urllib.request, json

doc = {
    'schema_id': 'TEGAKI_AUTHORING_DOCUMENT',
    'schema_version': '1.0.0',
    'pages': [{
        'page_id': 'page_job_b_ref_test',
        'width_px': 832,
        'height_px': 1216,
        'style_prompt': 'monochrome manga, clean line art',
        'style_negative_prompt': '',
        'scenes': [{
            'scene_id': 'scene_main',
            'order': 1,
            'input_mode': 'cast',
            'prompt': 'standing outdoors, autumn park, falling leaves',
            'negative_prompt': '',
            'area': {'shape_type': 'rect', 'x': 0.0, 'y': 0.0, 'w': 1.0, 'h': 1.0}
        }],
        'guides': [],
        'cast': [{
            'cast_id': 'cast_heroine',
            'display_name': 'Heroine',
            'identity_prompt': '1girl, long hair, school uniform, detailed eyes',
            'negative_prompt': '',
            'reference_asset': 'tegaki_manga_references/ref_c789751db904319d.png'
        }],
        'character_instances': [{
            'instance_id': 'inst_heroine',
            'cast_id': 'cast_heroine',
            'scene_id': 'scene_main',
            'area': {'shape_type': 'rect', 'x': 0.1, 'y': 0.1, 'w': 0.8, 'h': 0.8},
            'acting_prompt': 'looking at viewer, gentle smile'
        }],
        'visual_frames': []
    }],
    'metadata': {}
}

caps = json.loads(urllib.request.urlopen('http://127.0.0.1:8191/api/manga/generation/capabilities').read().decode())
revision = caps['revision']

settings = {
    'request_id': 'req_job_b_ref_001',
    'mode': 'scene',
    'checkpoint_id': '!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors',
    'authoring_document': doc,
    'page_index': 0,
    'sampler_id': 'euler',
    'scheduler_id': 'normal',
    'steps': 24,
    'cfg': 5.0,
    'seed_requested': '240925',
    'capability_revision': revision,
    'mask_feather': 16,
    'panel_strength': 1.0
}

req = urllib.request.Request(
    'http://127.0.0.1:8191/api/manga/generation/compile-scene',
    data=json.dumps(settings).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print('Compile ok:', res.get('ok'))
        print('Graph digest:', res.get('graph_digest'))
        print('Effective seed:', res.get('effective_seed'))
        print('Audit trail reference:', res.get('audit_trail', {}).get('reference'))
        print('Audit trail scenes:', json.dumps(res.get('audit_trail', {}).get('scenes'), indent=2))
        graph = res.get('graph', {})
        print('Graph node count:', len(graph))
        for k in sorted(graph.keys(), key=int):
            print(f"Node {k}: {graph[k]['class_type']} -> {graph[k]['inputs']}")
except urllib.error.HTTPError as e:
    print('Compile HTTP error:', e.code, e.read().decode())

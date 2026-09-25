import urllib.request, json

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

caps = json.loads(urllib.request.urlopen('http://127.0.0.1:8191/api/manga/generation/capabilities').read().decode())
revision = caps['revision']

settings = {
    'request_id': 'req_job_a_guide_001',
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
        print('Audit trail controlnet:', res.get('audit_trail', {}).get('controlnet'))
        graph = res.get('graph', {})
        print('Graph node count:', len(graph))
        for k in sorted(graph.keys(), key=int):
            print(f"Node {k}: {graph[k]['class_type']} -> {graph[k]['inputs']}")
except urllib.error.HTTPError as e:
    print('Compile HTTP error:', e.code, e.read().decode())

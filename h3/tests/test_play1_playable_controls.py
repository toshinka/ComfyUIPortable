"""H3-PLAY1 deterministic compile/capability/submit tests. No real Native calls."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from h3.adapters import native_t2v as t, native_i2v as i, native_ref2va as r, native_still as still
from h3.adapters.playable_controls import DEFAULT_MODELS, capability_from_object_info, validate_selection
from h3.app.server import H1ASession, BackendClient, BackendError, BackendProfileError

FL = DEFAULT_MODELS['standard']
REF = DEFAULT_MODELS['reference']
ALT_FL = 'variants/minimax_h3_fl2va_fp16.safetensors'
ALT_REF = 'minimax_h3_ref2va_fp16.safetensors'
PAYLOAD = {'prompt': 'PLAY1 baseline', 'seed': 123}

def object_info():
    return {
        'UNETLoader': {'input': {'required': {'unet_name': [[FL, REF, ALT_FL, ALT_REF, 'sdxl.safetensors', '../minimax_h3_fl2va_bad.safetensors', 'minimax_h3_vae.safetensors']]}}, 'output': ['MODEL']},
        'LoraLoaderModelOnly': {'input': {'required': {'model': ['MODEL'], 'lora_name': [['a.safetensors', 'sub/b.safetensors', 'c.safetensors']], 'strength_model': ['FLOAT', {'min': -100, 'max': 100}]}}, 'output': ['MODEL']},
    }

def digest(graph):
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

# Independently computed using the unmodified adapters and workflows at
# e835892635d5323d1160765c6e56a9e42db2772b, with PAYLOAD and inputs/a.png, inputs/m.mp4.
BASE_HASHES = {
    'standard': '7152e80b66c5158e9dc8a600f8be3648998d0fc915a6ba9e05e761c6c0553317',
    'still': '10aa6be3d3873ac07f0c481b370c118148abde527956db602c0c3c8ab2309cd0',
    'start_frame': 'f9c6727f2814eefba8ab892417c8aa22ecf3854a41736286fc1549aaaee620ca',
    'end_frame': 'eea464febe274937a693a6fd4b95bb0bc53fb65d50dd1fe2a68ca0fbe22af021',
    'start_frame+end_frame': '4cf51457d1bd6a29fb8a4f75b2e0efa8900a1ba4976f42847b78d7e0c7291b1e',
    'reference': '8dd6a037adc8c6939dfe889586a2145b66f807ec00618f00cf789764afbdb688',
    'reference_motion': 'd9290015a58b0868cb6f1ecdb9d8801d235a2209f8d1c201c74c643597043392',
}

class PlayableAdapterTests(unittest.TestCase):
    def setUp(self):
        self.cap = capability_from_object_info(object_info())

    def graphs(self, overrides=None, reference_overrides=None):
        payload = {**PAYLOAD, **(overrides or {})}
        graphs = {'standard': t.compile_workflow(payload, capability=self.cap)}
        for roles in (('start_frame',), ('end_frame',), ('start_frame', 'end_frame')):
            request = {**payload, 'references': {role: {'id': 'a'*32, 'role': role} for role in roles}}
            graphs['+'.join(roles)] = i.compile_fl2va_workflow(request, {role: 'inputs/a.png' for role in roles}, capability=self.cap)
        for motion in (None, 'inputs/m.mp4'):
            graphs['reference_motion' if motion else 'reference'] = r.compile_workflow(
                r.H3Ref2VARequest(**PAYLOAD, picture_path='inputs/a.png', video_path=motion, **(reference_overrides or {})), capability=self.cap)
        return graphs

    def test_A_H_L_M_N_O_all_baselines_equal_exact_base(self):
        for graphs in (self.graphs(), self.graphs({'model_name': FL, 'loras': []}, {'model_name': REF, 'loras': []})):
            graphs['still'] = still.compile_workflow(still.H3StillRequest(**PAYLOAD))
            for name, graph in graphs.items():
                with self.subTest(route=name):
                    self.assertEqual(digest(graph), BASE_HASHES[name])
                    self.assertEqual(graph['126']['inputs']['model'], ['127', 0])

    def test_B_C_E_size_duration_grid_all_routes(self):
        for width, height in ((512,288), (608,352), (736,416)):
            for duration in (3,5,10,15):
                for name, graph in self.graphs({'width':width,'height':height,'duration':duration}, {'width':width,'height':height,'duration_seconds':duration}).items():
                    with self.subTest(size=(width,height),duration=duration,route=name):
                        self.assertEqual((graph['131']['inputs']['width'],graph['131']['inputs']['height']), (width,height))
                        self.assertEqual(graph['131']['inputs']['length'], t.duration_to_frames(duration))
                        if name == 'reference_motion': self.assertEqual(graph['136']['inputs']['duration'],duration)

    def test_D_duration_rejections(self):
        for value in (0,2,7,15.1,16,100,True,None,float('nan'),float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): t.validate_request({**PAYLOAD,'duration':value})
                with self.assertRaises(ValueError): r.H3Ref2VARequest(**PAYLOAD,picture_path='inputs/a.png',duration_seconds=value)
        for size in ((864,480),(512,352),(1024,576)):
            with self.assertRaises(ValueError): t.validate_request({**PAYLOAD,'width':size[0],'height':size[1]})

    def test_F_override_reaches_loader_all_routes(self):
        for name, graph in self.graphs({'model_name':ALT_FL},{'model_name':ALT_REF}).items():
            self.assertEqual(graph['127']['inputs']['unet_name'], ALT_REF if name.startswith('reference') else ALT_FL)

    def test_G_unknown_route_incompatible_and_unverified_fail_closed(self):
        for model in ('missing.safetensors', REF, 'C:/secret/model.safetensors', '../'+FL):
            with self.assertRaises(ValueError): t.compile_workflow({**PAYLOAD,'model_name':model},capability=self.cap)
        with self.assertRaises(ValueError): t.compile_workflow({**PAYLOAD,'model_name':FL})
        with self.assertRaises(ValueError): r.compile_workflow(r.H3Ref2VARequest(**PAYLOAD,picture_path='inputs/a.png',model_name=FL),capability=self.cap)

    def test_I_J_order_and_model_only_edges_all_routes(self):
        entries=[{'name':'a.safetensors','strength':0.8},{'name':'sub/b.safetensors','strength':-2},{'name':'c.safetensors','strength':2}]
        for count in (1,2,3):
            stack=entries[:count]
            baseline=self.graphs()
            for name,graph in self.graphs({'loras':stack},{'loras':stack}).items():
                self.assertEqual(graph['128'],baseline[name]['128'])
                for index,item in enumerate(stack):
                    node=graph[f'h3_play1_lora_{index+1}']
                    self.assertEqual(node,{'class_type':'LoraLoaderModelOnly','inputs':{'model':['127' if index==0 else f'h3_play1_lora_{index}',0],'lora_name':item['name'],'strength_model':item['strength']}})
                for consumer in ('124','126'):
                    self.assertEqual(graph[consumer]['inputs']['model'],[f'h3_play1_lora_{count}',0])

    def test_K_missing_invalid_lora(self):
        for strength in (-2.1,2.1,True,None,'1',float('nan'),float('inf')):
            with self.assertRaises(ValueError): t.validate_request({**PAYLOAD,'loras':[{'name':'a.safetensors','strength':strength}]})
        for stack in (None,{},[{'name':'a.safetensors'}],[{'name':'a.safetensors','strength':1}]*4,[{'name':'../a.safetensors','strength':1}]):
            with self.assertRaises(ValueError): t.validate_request({**PAYLOAD,'loras':stack})
        for stack in ([{'name':'missing.safetensors','strength':1}], [{'name':'a.safetensors','strength':1}]):
            cap=deepcopy(self.cap)
            cap['lora']['names']=[]
            with self.assertRaises(ValueError): t.compile_workflow({**PAYLOAD,'loras':stack},capability=cap)

    def test_capability_filter_and_optional_loader(self):
        self.assertEqual(self.cap['models'],{'standard':[FL,ALT_FL],'reference':[REF,ALT_REF]})
        self.assertEqual(self.cap['lora']['state'],'AVAILABLE')
        for loader in (None,{}, {'input':{'required':{'model':[]}}}, {'output':['MODEL','CLIP']}, {'input':None}):
            info=object_info(); info['LoraLoaderModelOnly']=loader
            cap=capability_from_object_info(info)
            self.assertEqual(cap['lora']['state'],'UNAVAILABLE')
            t.compile_workflow({**PAYLOAD,'model_name':FL},capability=cap)
            with self.assertRaises(ValueError): t.compile_workflow({**PAYLOAD,'loras':[{'name':'a.safetensors','strength':1}]},capability=cap)

class PlayableServerTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.session=H1ASession('http://127.0.0.1:9',Path(temp.name))
        self.info=object_info(); self.calls=[]
        self.backend=self.session.backend
        self.backend.status=Mock(return_value={'state':'READY'})
        def request(method,path,payload=None,timeout=None):
            self.calls.append((method,path,deepcopy(payload)))
            if method=='GET' and path=='/object_info': return deepcopy(self.info)
            if method=='POST' and path=='/prompt': return {'prompt_id':'fake-only'}
            raise AssertionError((method,path))
        self.backend._request=request

    def test_fresh_submit_revalidates_disappeared_model_and_retains_inputs(self):
        self.session.playable_capability()
        self.info['UNETLoader']['input']['required']['unet_name'][0].remove(ALT_FL)
        payload={**PAYLOAD,'model_name':ALT_FL}; before=deepcopy(payload)
        with self.assertRaises(ValueError): self.session.submit(payload)
        self.assertEqual(payload,before); self.assertFalse(self.session.jobs)
        self.assertFalse(any(method=='POST' for method,_,_ in self.calls))
        self.assertEqual(sum(path=='/object_info' for _,path,_ in self.calls),2)

    def test_missing_lora_prevents_compile_and_prompt(self):
        payload={**PAYLOAD,'model_name':FL,'loras':[{'name':'a.safetensors','strength':1}]}
        self.session.playable_capability()
        self.info['LoraLoaderModelOnly']['input']['required']['lora_name'][0]=[]
        with self.assertRaises(ValueError): self.session.submit(payload)
        self.assertFalse(any(method=='POST' for method,_,_ in self.calls)); self.assertFalse(self.session.jobs)

    def test_profile_mismatch_and_disconnection_fail_closed(self):
        self.backend.status=Mock(return_value={'state':'ERROR','backend_profile':'WRONG_PROFILE','backend_profile_detail':'test'})
        with self.assertRaises(BackendProfileError): self.session.submit({**PAYLOAD,'model_name':FL})
        self.assertFalse(self.calls)
        self.backend.status=Mock(side_effect=BackendError('offline'))
        self.assertEqual(self.session.playable_capability()['lora']['state'],'UNVERIFIED')
        with self.assertRaises(BackendError): self.session.submit({**PAYLOAD,'model_name':FL})
        self.assertFalse(self.session.jobs)

    def test_real_submit_boundary_receives_selected_graph_and_history(self):
        payload={**PAYLOAD,'width':512,'height':288,'duration':3,'model_name':ALT_FL,'loras':[{'name':'a.safetensors','strength':0.8}]}
        job=self.session.submit(payload)
        graph=self.calls[-1][2]['prompt']
        self.assertEqual(graph['127']['inputs']['unet_name'],ALT_FL)
        self.assertEqual(job.public()['request']['loras'],payload['loras'])
        self.assertEqual(job.public()['request']['model_name'],ALT_FL)
        self.assertEqual(self.backend.status.call_count,2)

    def test_reference_gate_uses_available_family_not_default_filename(self):
        self.info['UNETLoader']['input']['required']['unet_name'][0].remove(REF)
        self.backend.reference_node_available=Mock(return_value=True)
        capability=self.session.playable_capability()
        self.assertTrue(self.session.reference_video_capability(capability)['enabled'])
        capability['models']['reference']=[]
        self.assertFalse(self.session.reference_video_capability(capability)['enabled'])

    def test_reference_submit_selection_and_history(self):
        buffer=io.BytesIO(); Image.new('RGB',(16,16),'red').save(buffer,format='PNG')
        picture=self.session.upload_r2v_picture('picture.png',buffer.getvalue())
        payload={**PAYLOAD,'picture_id':picture.picture_id,'model_name':ALT_REF,'width':736,'height':416,'duration':10,'loras':[{'name':'sub/b.safetensors','strength':1}]}
        job=self.session.submit_reference_video(payload)
        self.assertEqual(self.calls[-1][2]['prompt']['127']['inputs']['unet_name'],ALT_REF)
        self.assertEqual(job.public()['request']['duration'],10)
        self.assertEqual(job.public()['request']['loras'],payload['loras'])

if __name__=='__main__': unittest.main()

# Copyright 2020 kubeflow.org
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import re
import shutil
import sys
import tempfile
import textwrap
import unittest
import yaml

from os import environ as env

from kfp_tekton import compiler


# temporarily set this flag to True in order to (re)generate new "golden" YAML
# files after making code changes that modify the expected YAML output.
# to (re)generate all "golden" YAML files from the command line run:
#    GENERATE_GOLDEN_YAML=True sdk/python/tests/run_tests.sh
# or:
#    make unit_test GENERATE_GOLDEN_YAML=True
GENERATE_GOLDEN_YAML = env.get("GENERATE_GOLDEN_YAML", "False") == "True"

if GENERATE_GOLDEN_YAML:
  logging.warning(
    "The environment variable 'GENERATE_GOLDEN_YAML' was set to 'True'. Test cases will regenerate "
    "the 'golden' YAML files instead of verifying the YAML produced by compiler.")

# License header for Kubeflow project
LICENSE_HEADER = textwrap.dedent("""\
# Copyright 2020 kubeflow.org
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""")


class TestTektonCompiler(unittest.TestCase):

  def test_init_container_workflow(self):
    """
    Test compiling a initial container workflow.
    """
    from .testdata.init_container import init_container_pipeline
    self._test_pipeline_workflow(init_container_pipeline, 'init_container.yaml')

  def test_condition_workflow(self):
    """
    Test compiling a conditional workflow
    """
    from .testdata.condition import flipcoin
    self._test_pipeline_workflow(flipcoin, 'condition.yaml')

  def test_sequential_workflow(self):
    """
    Test compiling a sequential workflow.
    """
    from .testdata.sequential import sequential_pipeline
    self._test_pipeline_workflow(sequential_pipeline, 'sequential.yaml')

  def test_parallel_join_workflow_without_artifacts(self):
    """
    Test compiling a parallel join workflow.
    """
    from .testdata.parallel_join import download_and_join
    self._test_pipeline_workflow(download_and_join, 'parallel_join.yaml', enable_artifacts=False)

  def test_parallel_join_workflow_with_artifacts(self):
    """
    Test compiling a parallel join workflow with artifacts.
    """
    from .testdata.parallel_join import download_and_join
    self._test_pipeline_workflow(download_and_join, 'parallel_join_with_artifacts.yaml', enable_artifacts=True)

  def test_parallel_join_workflow_with_logging(self):
    """
    Test compiling a parallel join workflow with logging.
    """
    from .testdata.parallel_join import download_and_join
    self._test_pipeline_workflow(download_and_join, 'parallel_join_with_logging.yaml',
                                 enable_artifacts=False, enable_s3_logs=True)

  def test_parallel_join_with_argo_vars_workflow(self):
    """
    Test compiling a parallel join workflow.
    """
    from .testdata.parallel_join_with_argo_vars import download_and_join_with_argo_vars
    self._test_pipeline_workflow(download_and_join_with_argo_vars, 'parallel_join_with_argo_vars.yaml')

  def test_sidecar_workflow(self):
    """
    Test compiling a sidecar workflow.
    """
    from .testdata.sidecar import sidecar_pipeline
    self._test_pipeline_workflow(sidecar_pipeline, 'sidecar.yaml')
  
  def test_loop_static_workflow(self):
    """
    Test compiling a loop static params in workflow.
    """
    from .testdata.loop_static import pipeline
    self._test_pipeline_workflow(
      pipeline,
      'loop_static.yaml',
      normalize_compiler_output_function=lambda f: re.sub(
          "loop-item-param-.*-subvar", "loop-item-param-subvar", f))

  def test_withitem_nested_workflow(self):
    """
    Test compiling a withitem nested in workflow.
    """
    from .testdata.withitem_nested import pipeline
    self._test_pipeline_workflow(pipeline, 'withitem_nested.yaml')

  def test_pipelineparams_workflow(self):
    """
    Test compiling a pipelineparams workflow.
    """
    from .testdata.pipelineparams import pipelineparams_pipeline
    self._test_pipeline_workflow(pipelineparams_pipeline, 'pipelineparams.yaml')

  def test_retry_workflow(self):
    """
    Test compiling a retry task in workflow.
    """
    from .testdata.retry import retry_sample_pipeline
    self._test_pipeline_workflow(retry_sample_pipeline, 'retry.yaml')

  def test_volume_workflow(self):
    """
    Test compiling a volume workflow.
    """
    from .testdata.volume import volume_pipeline
    self._test_pipeline_workflow(volume_pipeline, 'volume.yaml')

  def test_timeout_workflow(self):
    """
    Test compiling a step level timeout workflow.
    """
    from .testdata.timeout import timeout_sample_pipeline
    self._test_pipeline_workflow(timeout_sample_pipeline, 'timeout.yaml')

  def test_resourceOp_workflow(self):
    """
    Test compiling a resourceOp basic workflow.
    """
    from .testdata.resourceop_basic import resourceop_basic
    self._test_pipeline_workflow(resourceop_basic, 'resourceop_basic.yaml')

  def test_volumeOp_workflow(self):
    """
    Test compiling a volumeOp basic workflow.
    """
    from .testdata.volume_op import volumeop_basic
    self._test_pipeline_workflow(volumeop_basic, 'volume_op.yaml')

  def test_volumeSnapshotOp_workflow(self):
    """
    Test compiling a volumeSnapshotOp basic workflow.
    """
    from .testdata.volume_snapshot_op import volume_snapshotop_sequential
    self._test_pipeline_workflow(volume_snapshotop_sequential, 'volume_snapshot_op.yaml')

  def test_hidden_output_file_workflow(self):
    """
    Test compiling a workflow with non configurable output file.
    """
    from .testdata.hidden_output_file import hidden_output_file_pipeline
    self._test_pipeline_workflow(hidden_output_file_pipeline, 'hidden_output_file.yaml')

  def test_tolerations_workflow(self):
    """
    Test compiling a tolerations workflow.
    """
    from .testdata.tolerations import tolerations
    self._test_pipeline_workflow(tolerations, 'tolerations.yaml')

  def test_affinity_workflow(self):
    """
    Test compiling a affinity workflow.
    """
    from .testdata.affinity import affinity_pipeline
    self._test_pipeline_workflow(affinity_pipeline, 'affinity.yaml')

  def test_node_selector_workflow(self):
    """
    Test compiling a node selector workflow.
    """
    from .testdata.node_selector import node_selector_pipeline
    self._test_pipeline_workflow(node_selector_pipeline, 'node_selector.yaml')

  def test_pipeline_transformers_workflow(self):
    """
    Test compiling a pipeline_transformers workflow with pod annotations and labels.
    """
    from .testdata.pipeline_transformers import transform_pipeline
    self._test_pipeline_workflow(transform_pipeline, 'pipeline_transformers.yaml')

  def test_input_artifact_raw_value_workflow(self):
    """
    Test compiling an input artifact workflow.
    """
    from .testdata.input_artifact_raw_value import input_artifact_pipeline
    self._test_pipeline_workflow(input_artifact_pipeline, 'input_artifact_raw_value.yaml')

  def test_big_data_workflow(self):
    """
    Test compiling a big data passing workflow.
    """
    from .testdata.big_data_passing import file_passing_pipelines
    self._test_pipeline_workflow(file_passing_pipelines, 'big_data_passing.yaml')

  def test_katib_workflow(self):
    """
    Test compiling a katib workflow.
    """
    # dictionaries and lists do not preserve insertion order before Python 3.6.
    # katib.py uses (string-serialized) dictionaries containing dsl.PipelineParam objects
    # which can't be JSON-serialized so using json.dumps(sorted) is not an alternative
    if sys.version_info < (3, 6, 0):
      logging.warning("Skipping katib workflow test for Python version < 3.6.0")
    else:
      from .testdata.katib import mnist_hpo
      self._test_pipeline_workflow(mnist_hpo, 'katib.yaml')

  def test_load_from_yaml_workflow(self):
    """
    Test compiling a pipeline with components loaded from yaml.
    """
    from .testdata.load_from_yaml import component_yaml_pipeline
    self._test_pipeline_workflow(component_yaml_pipeline, 'load_from_yaml.yaml')
    
  def test_imagepullsecrets_workflow(self):
    """
    Test compiling a imagepullsecrets workflow.
    """
    from .testdata.imagepullsecrets import imagepullsecrets_pipeline
    self._test_pipeline_workflow(imagepullsecrets_pipeline, 'imagepullsecrets.yaml')

  def test_basic_no_decorator(self):
    """
    Test compiling a basic workflow with no pipeline decorator
    """
    from .testdata import basic_no_decorator
    parameter_dict = {
      "function": basic_no_decorator.save_most_frequent_word,
      "name": 'Save Most Frequent Word',
      "description": 'Get Most Frequent Word and Save to GCS',
      "paramsList": [basic_no_decorator.message_param, basic_no_decorator.output_path_param]
    }
    self._test_workflow_without_decorator('basic_no_decorator.yaml', parameter_dict)

  def test_exit_handler_workflow(self):
    """
    Test compiling a exit handler workflow.
    """
    from .testdata.exit_handler import download_and_print
    self._test_pipeline_workflow(download_and_print, 'exit_handler.yaml')

  def test_compose(self):
    """
    Test compiling a simple workflow, and a bigger one composed from a simple one.
    """
    from .testdata import compose
    self._test_nested_workflow('compose.yaml', [compose.save_most_frequent_word, compose.download_save_most_frequent_word])
    
  def _test_pipeline_workflow(self,
                              pipeline_function,
                              pipeline_yaml,
                              enable_artifacts=True,
                              enable_s3_logs=False,
                              normalize_compiler_output_function=None):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    golden_yaml_file = os.path.join(test_data_dir, pipeline_yaml)
    temp_dir = tempfile.mkdtemp()
    compiled_yaml_file = os.path.join(temp_dir, 'workflow.yaml')
    try:
      compiler.TektonCompiler().compile(pipeline_function,
                                        compiled_yaml_file,
                                        enable_artifacts=enable_artifacts,
                                        enable_s3_logs=enable_s3_logs)
      with open(compiled_yaml_file, 'r') as f:
        f = normalize_compiler_output_function(
          f.read()) if normalize_compiler_output_function else f
        compiled = yaml.safe_load(f)
      self._verify_compiled_workflow(golden_yaml_file, compiled)
    finally:
      shutil.rmtree(temp_dir)

  def _test_workflow_without_decorator(self, pipeline_yaml, params_dict):
    """
    Test compiling a workflow and appending pipeline params.
    """
    test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    golden_yaml_file = os.path.join(test_data_dir, pipeline_yaml)
    temp_dir = tempfile.mkdtemp()
    try:
      compiled_workflow = compiler.TektonCompiler()._create_workflow(
          params_dict['function'],
          params_dict.get('name', None),
          params_dict.get('description', None),
          params_dict.get('paramsList', None),
          params_dict.get('conf', None))
      self._verify_compiled_workflow(golden_yaml_file, compiled_workflow)
    finally:
      shutil.rmtree(temp_dir)

  def _test_nested_workflow(self,
                            pipeline_yaml,
                            pipeline_list,
                            enable_artifacts=True,
                            normalize_compiler_output_function=None):
    """
    Test compiling a simple workflow, and a bigger one composed from the simple one.
    """
    test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    golden_yaml_file = os.path.join(test_data_dir, pipeline_yaml)
    temp_dir = tempfile.mkdtemp()
    compiled_yaml_file = os.path.join(temp_dir, 'nested' + str(len(pipeline_list) - 1) + '.yaml')
    try:
      for index, pipeline in enumerate(pipeline_list):
          package_path = os.path.join(temp_dir, 'nested' + str(index) + '.yaml')
          compiler.TektonCompiler().compile(pipeline,
                                            package_path,
                                            enable_artifacts=enable_artifacts)
      with open(compiled_yaml_file, 'r') as f:
        f = normalize_compiler_output_function(
          f.read()) if normalize_compiler_output_function else f
        compiled = yaml.safe_load(f)
      self._verify_compiled_workflow(golden_yaml_file, compiled)
    finally:
      shutil.rmtree(temp_dir)

  def _verify_compiled_workflow(self, golden_yaml_file, compiled_workflow):
    """
    Tests if the compiled workflow matches the golden yaml.
    """
    if GENERATE_GOLDEN_YAML:
      with open(golden_yaml_file, 'w') as f:
        f.write(LICENSE_HEADER)
      with open(golden_yaml_file, 'a+') as f:
        yaml.dump(compiled_workflow, f, default_flow_style=False)
    else:
      with open(golden_yaml_file, 'r') as f:
        golden = yaml.safe_load(f)
      self.maxDiff = None

      # sort dicts and lists, insertion order was not guaranteed before Python 3.6
      if sys.version_info < (3, 6, 0):
        def sort_items(obj):
          from collections import OrderedDict
          if isinstance(obj, dict):
            return OrderedDict({k: sort_items(v) for k, v in sorted(obj.items())})
          elif isinstance(obj, list):
            return sorted([sort_items(o) for o in obj], key=lambda x: str(x))
          else:
            return obj
        golden = sort_items(golden)
        compiled_workflow = sort_items(compiled_workflow)

      self.assertEqual(golden, compiled_workflow,
                       msg="\n===[ " + golden_yaml_file.split(os.path.sep)[-1] + " ]===\n"
                           + json.dumps(compiled_workflow, indent=2))

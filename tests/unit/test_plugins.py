import copy
import csv
import os.path as op

import pytest
from mock import Mock, call, patch, mock_open
from lxml.etree import ElementTree
import paths
import subprocess
import datetime
from AndroidRunner.Plugins.android.Android import Android
from AndroidRunner.Plugins.Profiler import Profiler
from AndroidRunner.Plugins.Profiler import ProfilerException
from AndroidRunner.Plugins.trepn.Trepn import Trepn
from AndroidRunner.Plugins.perfetto.Perfetto import Perfetto
import AndroidRunner.util as util

class TestPluginTemplate(object):
    @pytest.fixture()
    def profiler_template(self):
        return Profiler('config', [])

    @pytest.fixture()
    def mock_device(self):
        return Mock()

    def test_init(self):
        Profiler('config', [])

    def test_dependencies(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.dependencies()

    def test_load(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.load(mock_device)

    def test_start_profiling(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.start_profiling(mock_device)

    def test_stop_profiling(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.stop_profiling(mock_device)

    def test_collect_results(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.collect_results(mock_device)

    def test_unload(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.unload(mock_device)

    def test_set_output(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.set_output('output/dir')

    def test_aggregate_subject(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.aggregate_subject()

    def test_aggregate_end(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.aggregate_end('data/dir', 'output/file.csv')

class TestAndroidPlugin(object):
    @pytest.fixture()
    def mock_device(self):
        return Mock()

    @pytest.fixture()
    def fixture_dir(self):
        return op.join(op.dirname(op.abspath(__file__)), 'fixtures')

    @pytest.fixture()
    def android_plugin(self):
        test_config = {'sample_interval': 1000, 'data_points': ['cpu', 'mem']}
        test_paths = {'path1': 'path/1'}
        return Android(test_config, test_paths)

    @staticmethod
    def csv_reader_to_table(filename):
        result = []
        with open(filename, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                result.append(row)
        return result

    @staticmethod
    def get_dataset(filename):
        with open(filename, mode='r') as csv_file:
            dataset = set(map(tuple, csv.reader(csv_file)))
        return dataset

    @patch('AndroidRunner.Plugins.Profiler.__init__')
    def test_android_plugin_succes(self, super_init):
        test_config = {'sample_interval': 1000, 'data_points': ['cpu', 'mem']}
        test_paths = {'path1': 'path/1'}
        ap = Android(test_config, test_paths)

        super_init.assert_called_once_with(test_config, test_paths)
        assert ap.output_dir == ''
        assert ap.paths == test_paths
        assert ap.profile is False
        assert ap.interval == 1
        assert ap.data_points == ['cpu', 'mem']
        assert ap.data == [['datetime', 'cpu', 'mem']]

    @patch('logging.Logger.warning')
    def test_android_plugin_invalid_datapoints(self, logger_warning):
        test_config = {'sample_interval': 1000, 'data_points': ['cpu', 'mem', 'invalid']}
        test_paths = {'path1': 'path/1'}
        ap = Android(test_config, test_paths)

        assert ap.output_dir == ''
        assert ap.paths == test_paths
        assert ap.profile is False
        assert ap.interval == 1
        assert ap.data_points == ['cpu', 'mem']
        assert ap.data == [['datetime', 'cpu', 'mem']]
        logger_warning.assert_called_once_with("Invalid data points in config: ['invalid']")

    def test_android_plugin_default_interval(self):
        test_config = {'data_points': ['cpu', 'mem', 'invalid']}
        test_paths = {'path1': 'path/1'}
        ap = Android(test_config, test_paths)

        assert ap.output_dir == ''
        assert ap.paths == test_paths
        assert ap.profile is False
        assert ap.interval == 0
        assert ap.data_points == ['cpu', 'mem']
        assert ap.data == [['datetime', 'cpu', 'mem']]

    def test_get_cpu_usage(self, android_plugin, mock_device):
        mock_device.shell.return_value = '30% TOTAL: 21% user + 6.7% kernel + 1.2% iowait + 0.7% irq + 0.5% softirq'
        cpu_usage = android_plugin.get_cpu_usage(mock_device)

        assert cpu_usage == '30'
        mock_device.shell.assert_called_once_with('dumpsys cpuinfo | grep TOTAL')

    def test_get_cpu_usage_minus_in(self, android_plugin, mock_device):
        mock_device.shell.return_value = '30.-6% TOTAL: 21% user + 6.7% kernel + 1.2% iowait + 0.7% irq + 0.5% softirq'
        cpu_usage = android_plugin.get_cpu_usage(mock_device)

        assert cpu_usage == '30.6'
        mock_device.shell.assert_called_once_with('dumpsys cpuinfo | grep TOTAL')

    def test_get_mem_usage_no_app(self, android_plugin, mock_device):
        mock_device.shell.return_value = 'Used RAM: 1016104 kB (819528 used pss + 196576 kernel)'

        mem_usage = android_plugin.get_mem_usage(mock_device, None)

        assert mem_usage == "1016104"
        mock_device.shell.assert_called_once_with('dumpsys meminfo | grep Used')

    def test_get_mem_usage_app_found(self, android_plugin, mock_device):
        mock_device.shell.return_value = ' TOTAL    20411     7516    10228      980    36740    28499     8240   ' \
                                         'TOTAL:    20411      TOTAL SWAP (KB):      980'

        mem_usage = android_plugin.get_mem_usage(mock_device, 'com.google.android.calendar')

        assert mem_usage == "20411"
        mock_device.shell.assert_called_once_with('dumpsys meminfo com.google.android.calendar | grep TOTAL')

    def test_get_mem_usage_app_not_found(self, android_plugin, mock_device):
        mock_device.shell.side_effect = ['', 'No process found for: fake.app']

        with pytest.raises(Exception) as exception:
            android_plugin.get_mem_usage(mock_device, 'fake.app')

        assert str(exception.value) == 'Android Profiler: No process found for: fake.app'
        mock_device.shell.mock_calls[0]('dumpsys meminfo fake.app | grep TOTAL')
        mock_device.shell.mock_calls[1]('dumpsys meminfo fake.app')

    @patch('AndroidRunner.Plugins.android.Android.Android.get_data')
    def test_start_profiling_with_app(self, get_data_mock, android_plugin, mock_device):
        kwargs = {'arg1': 1, 'app': 'test.app'}
        android_plugin.start_profiling(mock_device, **kwargs)

        assert android_plugin.profile is True
        get_data_mock.assert_called_once_with(mock_device, 'test.app')

    @patch('AndroidRunner.Plugins.android.Android.Android.get_data')
    def test_start_profiling_without_app(self, get_data_mock, android_plugin, mock_device):
        kwargs = {'arg1': 1}
        android_plugin.start_profiling(mock_device, **kwargs)

        assert android_plugin.profile is True
        get_data_mock.assert_called_once_with(mock_device, None)

    @patch('timeit.default_timer')
    @patch('threading.Timer')
    @patch('AndroidRunner.Plugins.android.Android.Android.get_cpu_usage')
    @patch('AndroidRunner.Plugins.android.Android.Android.get_mem_usage')
    def test_get_data_all_points(self, get_mem_usage_mock, get_cpu_usage_mock, timer_mock, timeit_mock,
                                 android_plugin, mock_device):
        timeit_mock.side_effect = [100, 200]
        mock_device.shell.return_value = 'device_time'
        get_mem_usage_mock.return_value = "mem_usage"
        get_cpu_usage_mock.return_value = "cpu_usage"
        mock_timer_result = Mock()
        timer_mock.return_value = mock_timer_result
        android_plugin.profile = True
        android_plugin.interval = 200
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data[1] == ['device_time', 'cpu_usage', 'mem_usage']
        timer_mock.assert_called_once_with(100, android_plugin.get_data, args=(mock_device, 'app'))
        mock_timer_result.start.assert_called_once()

    def test_get_data_race(self, android_plugin, mock_device):
        android_plugin.profile = False

        old_data = copy.deepcopy(android_plugin.data)
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data == old_data

    @patch('timeit.default_timer')
    @patch('threading.Timer')
    @patch('AndroidRunner.Plugins.android.Android.Android.get_cpu_usage')
    @patch('AndroidRunner.Plugins.android.Android.Android.get_mem_usage')
    def test_get_data_only_mem(self, get_mem_usage_mock, get_cpu_usage_mock, timer_mock, timeit_mock,
                               android_plugin, mock_device):
        timeit_mock.side_effect = [100, 200]
        mock_device.shell.return_value = 'device_time'
        get_mem_usage_mock.return_value = "mem_usage"
        get_cpu_usage_mock.return_value = "cpu_usage"
        android_plugin.data_points = ['mem']
        android_plugin.profile = True
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data[1] == ['device_time', 'mem_usage']

    @patch('timeit.default_timer')
    @patch('threading.Timer')
    @patch('AndroidRunner.Plugins.android.Android.Android.get_cpu_usage')
    @patch('AndroidRunner.Plugins.android.Android.Android.get_mem_usage')
    def test_get_data_only_cpu(self, get_mem_usage_mock, get_cpu_usage_mock, timer_mock, timeit_mock,
                               android_plugin, mock_device):
        timeit_mock.side_effect = [100, 200]
        mock_device.shell.return_value = 'device_time'
        get_mem_usage_mock.return_value = "mem_usage"
        get_cpu_usage_mock.return_value = "cpu_usage"
        android_plugin.data_points = ['cpu']
        android_plugin.profile = True
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data[1] == ['device_time', 'cpu_usage']

    def test_stop_profiling(self, android_plugin, mock_device):
        android_plugin.profile = True

        android_plugin.stop_profiling(mock_device)

        assert android_plugin.profile is False

    @patch('time.strftime')
    def test_collect_results(self, time_mock, android_plugin, mock_device, tmpdir, fixture_dir):
        test_output_dir = str(tmpdir)
        time_mock.return_value = 'time'
        mock_device.id = 'device_id'
        time_mock.return_value = 'experiment_time'
        android_plugin.data = self.csv_reader_to_table(op.join(fixture_dir, 'test_android_output.csv'))
        android_plugin.output_dir = test_output_dir

        android_plugin.collect_results(mock_device)

        assert op.isfile(op.join(test_output_dir, '{}_{}.csv'.format('device_id', 'experiment_time')))

        file_content_created = self.get_dataset(
            op.join(test_output_dir, '{}_{}.csv'.format('device_id', 'experiment_time')))
        file_content_original = self.get_dataset(op.join(fixture_dir, 'test_android_output.csv'))
        assert file_content_created == file_content_original

    def test_set_output(self, android_plugin):
        test_output_dir = "asdfgbfsdgbf/hjbdsfavav"
        android_plugin.set_output(test_output_dir)

        assert android_plugin.output_dir == test_output_dir

    def test_dependencies(self, android_plugin):
        assert android_plugin.dependencies() == []

    def test_load(self, android_plugin, mock_device):
        assert android_plugin.load(mock_device) is None

    def test_unload(self, android_plugin, mock_device):
        assert android_plugin.unload(mock_device) is None

    @patch('AndroidRunner.util.write_to_file')
    @patch('AndroidRunner.Plugins.android.Android.Android.aggregate_android_subject')
    def test_aggregate_subject(self, aggregate_mock, write_to_file_mock, android_plugin):
        test_output_dir = 'test/output/dir'
        android_plugin.output_dir = test_output_dir
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        android_plugin.aggregate_subject()

        aggregate_mock.assert_called_once_with(test_output_dir)
        expected_list = list()
        expected_list.append(mock_rows)
        write_to_file_mock.assert_called_once_with(op.join(test_output_dir, 'Aggregated.csv'), expected_list)

    @patch('AndroidRunner.util.write_to_file')
    @patch('AndroidRunner.Plugins.android.Android.Android.aggregate_final')
    def test_aggregate_end(self, aggregate_mock, write_to_file_mock, android_plugin):
        test_data_dir = 'test/output/dir'
        test_output_file = 'test/output/file.csv'
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        android_plugin.aggregate_end(test_data_dir, test_output_file)

        aggregate_mock.assert_called_once_with(test_data_dir)
        write_to_file_mock.assert_called_once_with(test_output_file, mock_rows)

    def test_aggregate_android_subject(self, android_plugin, fixture_dir):
        test_subject_log_dir = op.join(fixture_dir, 'android_subject_result')

        test_logs_aggregated = android_plugin.aggregate_android_subject(test_subject_log_dir)
        assert len(test_logs_aggregated) == 2
        assert test_logs_aggregated['android_cpu'] == 32.94186117467583
        assert test_logs_aggregated['android_mem'] == 1131976.3141113652

    @patch("AndroidRunner.Plugins.android.Android.Android.aggregate_android_final")
    def test_aggregate_final_web(self, aggregate_mock, android_plugin, fixture_dir):
        test_struct_dir_web = op.join(fixture_dir, 'test_dir_struct', 'data_web')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = android_plugin.aggregate_final(test_struct_dir_web)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 4

    @patch("AndroidRunner.Plugins.android.Android.Android.aggregate_android_final")
    def test_aggregate_final_native(self, aggregate_mock, android_plugin, fixture_dir):
        test_struct_dir_native = op.join(fixture_dir, 'test_dir_struct', 'data_native')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = android_plugin.aggregate_final(test_struct_dir_native)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 3

    def test_aggregate_android_final(self, android_plugin, fixture_dir):
        test_log_dir = op.join(fixture_dir, 'aggregate_final', 'android')
        aggregated_final_rows = android_plugin.aggregate_android_final(test_log_dir)

        assert len(aggregated_final_rows) == 2
        assert aggregated_final_rows['android_cpu'] == '19.017852474323064'
        assert aggregated_final_rows['android_mem'] == '1280213.4222222222'

class TestPerfettoPlugin(object):

    @pytest.fixture()
    @patch("AndroidRunner.Plugins.Profiler.__init__")
    @patch("AndroidRunner.util.load_json")
    def perfetto_plugin(self, load_json_mock, super_mock):
        super_mock.return_value = None
        load_json_mock.return_value = {}
        config = {"config_file" : "/home/user/perfetto_config.pbtx", "config_file_format" : "text"}
        test_paths = paths.paths_dict()
        return Perfetto(config, test_paths)

    @pytest.fixture()
    def mock_device(self):
        return Mock()

    @patch('AndroidRunner.Plugins.Profiler.__init__')
    @patch("AndroidRunner.util.load_json")
    def test_init(self, load_json_mock, super_mock):
        config_mock = Mock()
        test_paths = paths.paths_dict()
        config = {"config_file" : "perfetto_config.pbtx", "config_file_format" : "text"}
        load_json_mock.return_value = {}
        perfetto_plugin = Perfetto(config, test_paths)

        super_mock.assert_called_once_with(config, test_paths)
        assert perfetto_plugin.perfetto_trace_file_device_path  == ""
        assert perfetto_plugin.perfetto_config_file_device_path == ""
        assert perfetto_plugin.paths == paths.paths_dict()
        assert perfetto_plugin.perfetto_config_file_local_path == config["config_file"]
        assert perfetto_plugin.perfetto_config_file_format == config["config_file_format"]
        assert perfetto_plugin.adb_path == "adb"
    
    def test_dependencies(self, perfetto_plugin):
        assert perfetto_plugin.dependencies() == []

    def test_load(self, perfetto_plugin, mock_device, tmpdir):
        config_file = tmpdir.mkdir("config_files").join("perfetto_config.pbtx")
        config_file.write("Perfetto config file")
        perfetto_plugin.perfetto_config_file_local_path = str(config_file)
        perfetto_plugin.load(mock_device)

        assert perfetto_plugin.perfetto_config_file_device_path == op.join(perfetto_plugin.PERFETTO_CONFIG_DEVICE_PATH, "perfetto_config.pbtx")
        mock_device.push.assert_called_with(perfetto_plugin.perfetto_config_file_local_path, perfetto_plugin.perfetto_config_file_device_path)

    def test_load_file_not_found(self, perfetto_plugin, mock_device):
        perfetto_plugin.perfetto_config_file_local_path = "/home/user/no_file.pbtx"

        with pytest.raises(util.ConfigError) as except_result:
            perfetto_plugin.load(mock_device)

        assert "Config file not found on host. Is /home/user/no_file.pbtx the correct path?" in str(except_result)

    def test_set_output(self, perfetto_plugin, tmpdir):
        test_output_dir = str(tmpdir)
        
        perfetto_plugin.set_output(test_output_dir)

        assert perfetto_plugin.output_dir == test_output_dir

    @patch("AndroidRunner.Plugins.perfetto.Perfetto.subprocess.Popen")
    @patch("AndroidRunner.Plugins.perfetto.Perfetto.Perfetto._datetime_now")
    def test_start_profiling_text_config(self, datetime_mock, subprocess_mock, perfetto_plugin, mock_device):
        datetime_mock.return_value = datetime.datetime(2020, 12, 31, 21, 40, 22, 610621)
        popen_mock = Mock()
        popen_mock.communicate.return_value = (b"42", b"")
        mock_device.id = 20
        subprocess_mock.return_value = popen_mock

        perfetto_plugin.start_profiling(mock_device)

        assert perfetto_plugin.perfetto_trace_file_device_path == op.join(perfetto_plugin.PERFETTO_TRACES_DEVICE_PATH,
                 "2020_12_31T21_40_22_610621.perfetto_trace")
        assert perfetto_plugin.perfetto_device_pid == "42"
        subprocess_mock.assert_called_with(["adb", "-s", mock_device.id, "shell", f"cat {perfetto_plugin.perfetto_config_file_device_path} | perfetto --background --txt -c - -o {perfetto_plugin.perfetto_trace_file_device_path}"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @patch("AndroidRunner.Plugins.perfetto.Perfetto.subprocess.Popen")
    @patch("AndroidRunner.Plugins.perfetto.Perfetto.Perfetto._datetime_now")
    def test_start_profiling_binary_config(self, datetime_mock, subprocess_mock, perfetto_plugin, mock_device):
        datetime_mock.return_value = datetime.datetime(2020, 12, 31, 21, 40, 22, 610621)
        perfetto_plugin.perfetto_config_file_format = "binary"
        popen_mock = Mock()
        popen_mock.communicate.return_value = (b"42", b"")
        mock_device.id = 20
        subprocess_mock.return_value = popen_mock
        empty_string = ""

        perfetto_plugin.start_profiling(mock_device)

        assert perfetto_plugin.perfetto_trace_file_device_path == op.join(perfetto_plugin.PERFETTO_TRACES_DEVICE_PATH,
                 "2020_12_31T21_40_22_610621.perfetto_trace")
        assert perfetto_plugin.perfetto_device_pid == "42"
        subprocess_mock.assert_called_with(["adb", "-s", mock_device.id, "shell", f"cat {perfetto_plugin.perfetto_config_file_device_path} | perfetto --background {empty_string} -c - -o {perfetto_plugin.perfetto_trace_file_device_path}"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

 

    @patch("AndroidRunner.Plugins.perfetto.Perfetto.subprocess.Popen")
    def test_start_profiling_error(self, subprocess_mock, perfetto_plugin, mock_device):
        perfetto_plugin.perfetto_config_file_format = "binary"
        popen_mock = Mock()
        popen_mock.communicate.return_value = (b"", b"Error")
        mock_device.id = 20
        subprocess_mock.return_value = popen_mock

        with pytest.raises(ProfilerException):
            perfetto_plugin.start_profiling(mock_device)

    @patch("AndroidRunner.Plugins.perfetto.Perfetto.subprocess.Popen")
    def test_start_profiling_error_no_pid(self, subprocess_mock, perfetto_plugin, mock_device):
        perfetto_plugin.perfetto_config_file_format = "binary"
        popen_mock = Mock()
        popen_mock.communicate.return_value = (b"", b"")
        mock_device.id = 20
        mock_device.shell.return_value = "22"
        subprocess_mock.return_value = popen_mock

        perfetto_plugin.start_profiling(mock_device)
        assert perfetto_plugin.perfetto_device_pid == "22"
        mock_device.shell.assert_called_once_with("ps -A | grep perfetto | awk '{print $2}'")

    @patch("AndroidRunner.Plugins.perfetto.Perfetto.subprocess.Popen")
    def test_start_profiling_error_no_pid_ProfilerException(self, subprocess_mock, perfetto_plugin, mock_device):
        perfetto_plugin.perfetto_config_file_format = "binary"
        popen_mock = Mock()
        popen_mock.communicate.return_value = (b"", b"")
        mock_device.id = 20
        mock_device.shell.return_value = "22 23 24"
        subprocess_mock.return_value = popen_mock

        with pytest.raises(ProfilerException):
            perfetto_plugin.start_profiling(mock_device)

    def test_stop_profiling(self, mock_device, perfetto_plugin):
        perfetto_plugin.perfetto_device_pid = "42"
        perfetto_plugin.stop_profiling(mock_device)

        mock_device.shell.assert_called_once_with("kill 42")

    @patch("AndroidRunner.Plugins.perfetto.Perfetto.subprocess.Popen")
    @patch("builtins.open")
    def test_collect_results(self, open_mock, subprocess_mock, perfetto_plugin, mock_device) :
        m = mock_open()
        popen_mock = Mock()
        popen_mock.communicate.return_value = (b"42", b"")
        mock_device.id = 20
        subprocess_mock.return_value = popen_mock
        perfetto_plugin.perfetto_trace_file_device_path = op.join(perfetto_plugin.PERFETTO_TRACES_DEVICE_PATH, "filename.perfetto_trace")
        perfetto_plugin.paths["OUTPUT_DIR"] =  "/home/user/"
        filename =  "/home/user/filename.perfetto_trace"

        perfetto_plugin.collect_results(mock_device)

        open_mock.assert_called_once_with(filename, "w")
        mock_device.shell.assert_called_once_with(f"rm -f {perfetto_plugin.perfetto_trace_file_device_path}")

    def test_unload(self, mock_device, perfetto_plugin):
        perfetto_plugin.perfetto_config_file_device_path = "/sdcard/perfetto/trace.perfetto_trace"
        perfetto_plugin.unload(mock_device)

        mock_device.shell.assert_called_once_with(f"rm -Rf {perfetto_plugin.perfetto_config_file_device_path}")

class TestTrepnPlugin(object):

    @pytest.fixture()
    def fixture_dir(self):
        return op.join(op.dirname(op.abspath(__file__)), 'fixtures')

    @pytest.fixture()
    def mock_device(self):
        return Mock()
   
    @pytest.fixture()
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.build_preferences')
    @patch('AndroidRunner.Plugins.Profiler.__init__')
    def trepn_plugin(self, super_mock, build_preferences_mock):
        super_mock.return_value = None
        build_preferences_mock.return_value = None
        config_mock = Mock()
        test_paths = paths.paths_dict()
        return Trepn(config_mock, test_paths)

    @staticmethod
    def csv_reader_to_table(filename):
        result = []
        with open(filename, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                result.append(row)
        return result

    @staticmethod
    def file_content(filename):
        with open(filename, 'r') as myfile:
            content_string = myfile.read()
        return content_string

    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.build_preferences')
    @patch('AndroidRunner.Plugins.Profiler.__init__')
    def test_int(self, super_mock, build_preferences_mock):
        config_mock = Mock()
        test_paths = paths.paths_dict()
        trepn_plugin = Trepn(config_mock, test_paths)

        super_mock.assert_called_once_with(config_mock, test_paths)
        assert trepn_plugin.output_dir == ''
        assert trepn_plugin.paths == paths.paths_dict()
        assert trepn_plugin.pref_dir is None
        assert trepn_plugin.remote_pref_dir == op.join(trepn_plugin.DEVICE_PATH, 'saved_preferences/')
        build_preferences_mock.assert_called_once_with(config_mock)

    def test_dependencies(self, trepn_plugin):
        assert trepn_plugin.dependencies() == ['com.quicinc.trepn']

    def test_override_preferences_preference_not_in_params(self, trepn_plugin):
        test_params = {'NOTpreferences': {'profiling_interval': 300}, 'data_points': ['battery_power', 'mem_usage']}
        elem_tree = ElementTree()
        assert trepn_plugin.override_preferences(test_params, elem_tree) == elem_tree

    def test_build_preferences(self, trepn_plugin, tmpdir, fixture_dir):
        test_params = {'preferences': {'profiling_interval': 300, 'temperature_units': 'Celsius'}, 'data_points': ['battery_power', 'mem_usage']}
        trepn_plugin.paths['OUTPUT_DIR'] = str(tmpdir)

        trepn_plugin.build_preferences(test_params)

        expected_dir = op.join(trepn_plugin.paths['OUTPUT_DIR'], 'trepn.pref/')
        expected_pref_file = op.join(expected_dir, 'com.quicinc.trepn_preferences.xml')
        expected_dp_file = op.join(expected_dir, 'com.quicinc.preferences.saved_data_points.xml')
        assert trepn_plugin.pref_dir == expected_dir
        assert op.isdir(expected_dir)
        assert op.isfile(expected_pref_file)
        assert op.isfile(expected_dp_file)
        assert self.file_content(expected_pref_file) == self.file_content(op.join(fixture_dir, 'exp_trepn_pref.xml'))
        assert self.file_content(expected_dp_file) == self.file_content(op.join(fixture_dir, 'exp_saved_dp.xml'))

    @patch('time.sleep')
    def test_load(self, sleep_mock, trepn_plugin, mock_device, tmpdir):
        test_pref_dir = str(tmpdir)
        trepn_plugin.pref_dir = test_pref_dir
        mock_manager = Mock()
        mock_manager.attach_mock(sleep_mock, 'sleep_managed')
        mock_manager.attach_mock(mock_device, 'device_managed')

        trepn_plugin.load(mock_device)

        expected_calls = [call.device_managed.push(test_pref_dir, trepn_plugin.remote_pref_dir),
                          call.device_managed.launch_package('com.quicinc.trepn'),
                          call.sleep_managed(5),
                          call.device_managed.shell('am broadcast -a com.quicinc.trepn.load_preferences '
                                                    '-e com.quicinc.trepn.load_preferences_file "%s"'
                                                    % op.join(trepn_plugin.remote_pref_dir, 'trepn.pref')),
                          call.sleep_managed(1),
                          call.device_managed.force_stop('com.quicinc.trepn'),
                          call.sleep_managed(2),
                          call.device_managed.shell('am startservice com.quicinc.trepn/.TrepnService')]
        assert mock_manager.mock_calls == expected_calls

    def test_start_profiling(self, trepn_plugin, mock_device):
        trepn_plugin.start_profiling(mock_device)

        mock_device.shell.assert_called_once_with('am broadcast -a com.quicinc.trepn.start_profiling')

    def test_stop_profiling(self, trepn_plugin, mock_device):
        trepn_plugin.stop_profiling(mock_device)

        mock_device.shell.assert_called_once_with('am broadcast -a com.quicinc.trepn.stop_profiling')

    @patch('os.path.exists')
    @patch('AndroidRunner.util.wait_until')
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.filter_results')
    def test_collect_results(self, filter_results_mock, wait_until_mock, os_path_mock, trepn_plugin, mock_device, tmpdir):
        tmpdir_str = str(tmpdir)
        trepn_plugin.output_dir = tmpdir_str
        os_path_mock.return_value = True
        mock_device.id = '123'
        mock_device.shell.return_value = 'Trepn_2019.08.21_224812.db'
        mock_manager = Mock()
        mock_manager.attach_mock(mock_device, 'device_managed')
        mock_manager.attach_mock(wait_until_mock, 'wait_until_managed')
        mock_manager.attach_mock(filter_results_mock, 'filter_managed')

        trepn_plugin.collect_results(mock_device)

        expected_calls = [call.device_managed.shell(r'ls /sdcard/trepn/ | grep "\.db$"'),
                          call.device_managed.shell('am broadcast -a com.quicinc.trepn.export_to_csv '
                                                    '-e com.quicinc.trepn.export_db_input_file '
                                                    '"Trepn_2019.08.21_224812.db" '
                                                    '-e com.quicinc.trepn.export_csv_output_file '
                                                    '"123_Trepn_2019.08.21_224812.csv"'),
                          call.wait_until_managed(trepn_plugin.file_exists_and_not_empty, 5, 1, mock_device, trepn_plugin.DEVICE_PATH, "123_Trepn_2019.08.21_224812.csv" ),
                          call.device_managed.pull(op.join(trepn_plugin.DEVICE_PATH, '123_Trepn_2019.08.21_224812.csv')
                                                   , tmpdir_str),
                          call.wait_until_managed(os_path_mock, 5, 1, op.join(trepn_plugin.output_dir, "123_Trepn_2019.08.21_224812.csv")),
                          call.device_managed.shell(
                              'rm %s' % op.join(trepn_plugin.DEVICE_PATH, 'Trepn_2019.08.21_224812.db')),
                          call.device_managed.shell(
                              'rm %s' % op.join(trepn_plugin.DEVICE_PATH, '123_Trepn_2019.08.21_224812.csv')),
                          call.filter_managed(op.join(tmpdir_str, '123_Trepn_2019.08.21_224812.csv'))]
        assert mock_manager.mock_calls == expected_calls

    def test_file_exists_and_not_empty_file_found(self, mock_device, trepn_plugin):
        path_ = "/sdcard/trepn/"
        file_ = "123_Trepn_2019.08.21_224812.csv"

        mock_device.shell.side_effect = [f"Other data {file_} other data", "Not empty file contents"]
        res = trepn_plugin.file_exists_and_not_empty(mock_device, path_, file_)

        assert res == True

    def test_file_exists_and_not_empty_file_not_found(self, mock_device, trepn_plugin):
        path_ = "/sdcard/trepn/"
        file_ = "123_Trepn_2019.08.21_224812.csv"

        mock_device.shell.side_effect = [f"Other data other data", "Not empty file contents"]
        res = trepn_plugin.file_exists_and_not_empty(mock_device, path_, file_)

        assert res == False

    def test_file_exists_and_not_empty_file_empty(self, mock_device, trepn_plugin):
        path_ = "/sdcard/trepn/"
        file_ = "123_Trepn_2019.08.21_224812.csv"

        mock_device.shell.side_effect = [f"Other {file_} data other data", ""]
        res = trepn_plugin.file_exists_and_not_empty(mock_device, path_, file_)

        assert res == False

    def test_read_csv(self, trepn_plugin, fixture_dir):
        test_file = op.join(fixture_dir, 'test_trepn_data_to_filter.csv')
        assert trepn_plugin.read_csv(test_file) == self.csv_reader_to_table(test_file)

    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.write_list_to_file')
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.filter_data')
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.read_csv')
    def test_filter_result(self, read_csv_mock, filter_data_mock, write_mock, trepn_plugin, tmpdir, fixture_dir):
        test_filename = op.join(str(tmpdir), 'test_file.txt')
        test_data = self.csv_reader_to_table(op.join(fixture_dir, 'test_output_orig_trepn.csv'))
        read_csv_mock.return_value = test_data
        filter_data_result = Mock()
        filter_data_mock.return_value = filter_data_result
        statistic_to_filter_out = ['332', '328']
        trepn_plugin.data_points = statistic_to_filter_out

        trepn_plugin.filter_results(test_filename)
        read_csv_mock.assert_called_once_with(test_filename)
        write_mock.assert_called_once_with(test_filename, filter_data_result)
        filter_data_mock.assert_called_once_with(['Battery Power*', 'Memory Usage'], self.csv_reader_to_table(
            op.join(fixture_dir, 'test_trepn_data_to_filter.csv')))

    def test_write_list_to_file(self, trepn_plugin, tmpdir):
        test_filename = op.join(str(tmpdir), 'test_file.txt')
        test_data = [[], [], []]
        for i in range(0, 40):
            test_data[0].append('column_%s' % i)
            test_data[1].append('column_%s' % i)
            test_data[2].append('column_%s' % i)

        trepn_plugin.write_list_to_file(test_filename, test_data)

        assert op.isfile(test_filename)
        assert self.csv_reader_to_table(test_filename) == test_data

    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.filter_columns')
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.get_wanted_columns')
    def test_filter_data(self, get_wanted_columns_mock, filter_columns_mock, trepn_plugin):
        wanted_statistics_mock = Mock()
        data_mock = Mock()
        data_mock_list = [data_mock]
        wanted_columns_mock = Mock()
        get_wanted_columns_mock.return_value = wanted_columns_mock
        filtered_data_mock = Mock()
        filter_columns_mock.return_value = filtered_data_mock

        filtered_data = trepn_plugin.filter_data(wanted_statistics_mock, data_mock_list)

        get_wanted_columns_mock.assert_called_once_with(wanted_statistics_mock, data_mock)
        filter_columns_mock.assert_called_once_with(wanted_columns_mock, data_mock_list)
        assert filtered_data == filtered_data_mock

    def test_filter_columns(self, trepn_plugin):
        wanted_columns = [6, 7, 16, 17, 30, 31]
        data_columns = [[], []]
        for i in range(0, 40):
            data_columns[0].append('column_%s' % i)
            data_columns[1].append('column_%s' % i)
        remaining_data = trepn_plugin.filter_columns(wanted_columns, data_columns)
        assert len(remaining_data[0]) == len(remaining_data[1]) == 6
        for row in remaining_data:
            column_count = 0
            for column in row:
                assert column == 'column_%s' % wanted_columns[column_count]
                column_count += 1

    def test_get_wanted_columns(self, trepn_plugin):
        test_wanted_statistics = ['value_3', 'value_8', 'value_15']
        test_header_row = []
        for i in range(0, 30):
            test_header_row.append('Time [%s]' % i)
            test_header_row.append('value_%s [tst]' % i)

        result_columns = trepn_plugin.get_wanted_columns(test_wanted_statistics, test_header_row)

        assert result_columns == [6, 7, 16, 17, 30, 31]

    def test_unload(self, trepn_plugin, mock_device):
        trepn_plugin.unload(mock_device)

        expected_calls = [call.shell('am stopservice com.quicinc.trepn/.TrepnService'),
                          call.shell('rm -r %s' % op.join(trepn_plugin.remote_pref_dir, 'trepn.pref'))]
        assert mock_device.mock_calls == expected_calls

    def test_set_output(self, trepn_plugin, tmpdir):
        test_output_dir = str(tmpdir)

        trepn_plugin.set_output(test_output_dir)

        assert trepn_plugin.output_dir == test_output_dir

    @patch('AndroidRunner.util.write_to_file')
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.aggregate_trepn_subject')
    def test_aggregate_subject(self, aggregate_mock, write_to_file_mock, trepn_plugin):
        test_output_dir = 'test/output/dir'
        trepn_plugin.output_dir = test_output_dir
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        trepn_plugin.aggregate_subject()

        aggregate_mock.assert_called_once_with(test_output_dir)
        expected_list = list()
        expected_list.append(mock_rows)
        write_to_file_mock.assert_called_once_with(op.join(test_output_dir, 'Aggregated.csv'), expected_list)

    @patch('AndroidRunner.util.write_to_file')
    @patch('AndroidRunner.Plugins.trepn.Trepn.Trepn.aggregate_final')
    def test_aggregate_end(self, aggregate_mock, write_to_file_mock, trepn_plugin):
        test_data_dir = 'test/output/dir'
        test_output_file = 'test/output/file.csv'
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        trepn_plugin.aggregate_end(test_data_dir, test_output_file)

        aggregate_mock.assert_called_once_with(test_data_dir)
        write_to_file_mock.assert_called_once_with(test_output_file, mock_rows)

    def test_aggregate_trepn_subject(self, trepn_plugin, fixture_dir):
        test_subject_log_dir = op.join(fixture_dir, 'trepn_subject_result')

        test_logs_aggregated = trepn_plugin.aggregate_trepn_subject(test_subject_log_dir)

        assert len(test_logs_aggregated) == 4
        assert test_logs_aggregated['Battery Power* [uW] (Delta)'] == 1230355.5
        assert test_logs_aggregated['Battery Power* [uW] (Raw)'] == 2301245.088235294
        assert test_logs_aggregated['Battery Temperature [1/10 C]'] == 300.0
        assert test_logs_aggregated['Memory Usage [KB]'] == 2650836.2352941176

    @patch("AndroidRunner.Plugins.trepn.Trepn.Trepn.aggregate_trepn_final")
    def test_aggregate_final_web(self, aggregate_mock, trepn_plugin, fixture_dir):
        test_struct_dir_web = op.join(fixture_dir, 'test_dir_struct', 'data_web')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = trepn_plugin.aggregate_final(test_struct_dir_web)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 4

    @patch("AndroidRunner.Plugins.trepn.Trepn.Trepn.aggregate_trepn_final")
    def test_aggregate_final_native(self, aggregate_mock, trepn_plugin, fixture_dir):
        test_struct_dir_native = op.join(fixture_dir, 'test_dir_struct', 'data_native')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = trepn_plugin.aggregate_final(test_struct_dir_native)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 3

    def test_aggregate_trepn_final(self, trepn_plugin, fixture_dir):
        test_log_dir = op.join(fixture_dir, 'aggregate_final', 'trepn')
        aggregated_final_rows = trepn_plugin.aggregate_trepn_final(test_log_dir)

        assert len(aggregated_final_rows) == 4
        assert aggregated_final_rows['Battery Power* [uW] (Delta)'] == '1230355.5'
        assert aggregated_final_rows['Battery Power* [uW] (Raw)'] == '2301245.088235294'
        assert aggregated_final_rows['Battery Temperature [1/10 C]'] == '300.0'
        assert aggregated_final_rows['Memory Usage [KB]'] == '2650836.2352941176'

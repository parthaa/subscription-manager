import unittest
import sys
import socket

# to override config
import stubs

from subscription_manager import managercli
from stubs import MockStdout, MockStderr
from test_handle_gui_exception import FakeException, FakeLogger


class TestCliCommand(unittest.TestCase):
    command_class = managercli.CliCommand

    def setUp(self):
        self.cc = self.command_class()
        # neuter the _do_command, since this is mostly
        # for testing arg parsing
        self.cc._do_command = self._do_command
        self.cc.assert_should_be_registered = self._asert_should_be_registered

        # stub out uep
        managercli.connection.UEPConnection = self._uep_connection
        sys.stdout = MockStdout()
        sys.stderr = MockStderr()

    def tearDown(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def _uep_connection(self, *args, **kwargs):
        pass

    def _do_command(self):
        pass

    def _asert_should_be_registered(self):
        pass

    def test_main_no_args(self):
        try:
            self.cc.main()
        except SystemExit, e:
            # 2 == no args given
            self.assertEquals(e.code, 2)

    def _main_help(self, args):
        mstdout = MockStdout()
        sys.stdout = mstdout
        try:
            self.cc.main(args)
        except SystemExit, e:
            # --help/-h returns 0
            self.assertEquals(e.code, 0)
        sys.stdout = sys.__stdout__
        # I could test for strings here, but that
        # would break if we run tests in a locale/lang
        assert len(mstdout.buffer) > 0

    def test_main_short_help(self):
        self._main_help(["-h"])

    def test_main_long_help(self):
        self._main_help(["--help"])


# for command classes that expect proxy related cli args
class TestCliProxyCommand(TestCliCommand):
    def test_main_proxy_url(self):
        proxy_host = "example.com"
        proxy_port = "3128"
        proxy_url = "%s:%s" % (proxy_host, proxy_port)
        self.cc.main(["--proxy", proxy_url])
        self.assertEquals(proxy_url, self.cc.options.proxy_url)
        self.assertEquals(type(proxy_url), type(self.cc.options.proxy_url))
        self.assertEquals(proxy_host, self.cc.proxy_hostname)
        self.assertEquals(proxy_port, self.cc.proxy_port)

    def test_main_proxy_user(self):
        proxy_user = "buster"
        self.cc.main(["--proxyuser", proxy_user])
        self.assertEquals(proxy_user, self.cc.proxy_user)

    def test_main_proxy_password(self):
        proxy_password = "nomoresecrets"
        self.cc.main(["--proxypassword", proxy_password])
        self.assertEquals(proxy_password, self.cc.proxy_password)


class TestCleanCommand(TestCliCommand):
    command_class = managercli.CleanCommand


class TestRefreshCommand(TestCliProxyCommand):
    command_class = managercli.RefreshCommand


class TestIdentityCommand(TestCliProxyCommand):

    command_class = managercli.IdentityCommand

    def test_regenerate_no_force(self):
        self.cc.main(["--regenerate"])

# re, orgs
class TestOwnersCommand(TestCliProxyCommand):
    command_class = managercli.OwnersCommand

class TestEnvironmentsCommand(TestCliProxyCommand):
    command_class = managercli.EnvironmentsCommand

class TestRegisterCommand(TestCliProxyCommand):
    command_class = managercli.RegisterCommand

class TestListCommand(TestCliProxyCommand):
    command_class = managercli.ListCommand

    def setUp(self):
        self.indent = 1
        self.max_length = 40
        TestCliProxyCommand.setUp(self)

    def test_format_name_long(self):
        name = "This is a Really Long Name For A Product That We Do Not Want To See But Should Be Able To Deal With"
        formatted_name = self.cc._format_name(name, self.indent, self.max_length)

    def test_format_name_short(self):
        name = "a"
        formatted_name = self.cc._format_name(name, self.indent, self.max_length)

    def test_format_name_empty(self):
        name = 'e'
        formatted_name = self.cc._format_name(name, self.indent, self.max_length)

class TestUnRegisterCommand(TestCliProxyCommand):
    command_class = managercli.UnRegisterCommand


class TestRedeemCommand(TestCliProxyCommand):
    command_class = managercli.RedeemCommand


class TestReposCommand(TestCliCommand):
    command_class = managercli.ReposCommand


class TestConfigCommand(TestCliCommand):
    command_class = managercli.ConfigCommand

    def test_list(self):
        self.cc.main(["--list"])
        self.cc._validate_options()


class TestSubscribeCommand(TestCliProxyCommand):
    command_class = managercli.SubscribeCommand

    def _test_quantity_exception(self, arg):
        try:
            self.cc.main(["--auto", "--quantity", arg])
            self.cc._validate_options()
        except SystemExit, e:
            self.assertEquals(e.code, -1)
        else:
            self.fail("No Exception Raised")

    def test_zero_quantity(self):
        self._test_quantity_exception("0")

    def test_negative_quantity(self):
        self._test_quantity_exception("-1")

    def test_text_quantity(self):
        self._test_quantity_exception("JarJarBinks")

    def test_positive_quantity(self):
        self.cc.main(["--auto", "--quantity", "1"])
        self.cc._validate_options()


class TestUnSubscribeCommand(TestCliProxyCommand):
    command_class = managercli.UnSubscribeCommand


class TestFactsCommand(TestCliProxyCommand):
    command_class = managercli.FactsCommand

class TestImportCertCommand(TestCliCommand):
    command_class = managercli.ImportCertCommand

    def test_certificates(self):
        self.cc.main(["--certificate", "one", "--certificate", "two"])
        self.cc._validate_options()

    def test_no_certificates(self):
        try:
            self.cc.main([])
        except SystemExit, e:
            self.assertEquals(e.code, 2)

        try:
            self.cc._validate_options()
            self.fail("No exception raised")
        except Exception, e:
            pass
        except SystemExit, e:
            # there seems to be an optparse issue
            # here that depends on version, on f14
            # we get sysexit with return code 2  from main, on f15, we
            # get a -1 from validate_options
            # i18n_optparse returns 2 on no args
            self.assertEquals(e.code, -1)


class HandleExceptionTests(unittest.TestCase):
    def setUp(self):
        self.msg = "some thing to log home about"
        self.formatted_msg = "some thing else like: %s"
        managercli.log = FakeLogger()

    def test_he(self):
        e = FakeException()
        try:
            managercli.handle_exception(self.msg, e)
        except SystemExit, e:
            self.assertEquals(e.code, -1)

    def test_he_socket_error(self):
        # these error messages are bare strings, so we need to update the tests
        # if those messages change
        expected_msg = 'Network error, unable to connect to server. Please see /var/log/rhsm/rhsm.log for more information.'
        managercli.log.set_expected_msg(expected_msg)
        try:
            managercli.handle_exception(self.msg, socket.error())
        except SystemExit, e:
            self.assertEquals(e.code, -1)
        self.assertEqual(managercli.log.expected_msg, expected_msg)

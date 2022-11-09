import os
import re
import subprocess
import sys
import unittest

IRRD_HOST="fake.example.com"
IRRD_URL=f"http://{IRRD_HOST}"

UNRESOVABLE_HOST="www137xyz.example.com"
UNRESOVABLE_URL=f"http://{UNRESOVABLE_HOST}"

UNREACHABLE_HOST="localhost:65123" # just guessing
UNREACHABLE_URL=f"http://{UNREACHABLE_HOST}"

# example.com is for examples, but it resolves and there's a website
# that doesn't return JSON. That's handy for testing!
BAD_RESPONSE_HOST="www.example.com"
BAD_RESPONSE_URL=f"http://{BAD_RESPONSE_HOST}"

ENV_EMPTY = None
ENV_URL   = {"IRR_RPSL_SUBMIT_URL": IRRD_URL}
ENV_HOST  = {"IRR_RPSL_SUBMIT_HOST": IRRD_HOST}

REGEX_NO_OBJECTS    = re.compile("There were no RPSL objects in the input")
REGEX_ONE_OF        = re.compile("one of the arguments -h -u is required")
REGEX_NO_H_WITH_U   = re.compile("argument -h: not allowed with argument -u")
REGEX_UNRESOLVABLE  = re.compile("Could not resolve")
REGEX_UNREACHABLE   = re.compile("Connection refused")
REGEX_BAD_RESPONSE  = re.compile("decoding JSON")

EXIT_SUCCESS        =  0
EXIT_ARGUMENT_ERROR =  2
EXIT_INPUT_ERROR    =  4
EXIT_NETWORK_ERROR  =  8
EXIT_OTHER_ERROR    = 16

RPSL_EMPTY      = ""
RPSL_WHITESPACE = "\n\n\n    \t\t\n"
RPSL_MINIMAL    = "route: 1.2.3.4\norigin: AS65414\n"


class Runner():
    """
    Handle the details of running the external program
    """
    @classmethod
    def program(cls):
        return 'irr_rpsl_submit.py'

    @classmethod
    def program_args(cls, args):
        program = [ sys.executable, cls.program() ]
        program.extend(args)
        return program

    @classmethod
    def run(cls, args, env=None, rpsl=""):
        command = cls.program_args(args)
        print( "command:" )
        print( command )
        raw_result = subprocess.run(
            command,
            capture_output=True,
            encoding='utf-8',
            env=env,
            input=rpsl,
        )

        return raw_result

class Test(unittest.TestCase):
    def setUp(self):
        irr_env_names = [ 'IRR_RPSL_SUBMIT_DEBUG', 'IRR_RPSL_SUBMIT_HOST', 'IRR_RPSL_SUBMIT_URL' ]
        for name in irr_env_names:
            os.unsetenv(name)

    def tearDown(self):
        pass

    def test_010_nonense_options(self):
        for s in ['-Z', '-X', '-9', '--not-there' ]:
            result = Runner.run( [s], ENV_EMPTY, RPSL_EMPTY )
            self.assertEqual( result.returncode, EXIT_ARGUMENT_ERROR, f"nonsense switch {s} exits with {EXIT_ARGUMENT_ERROR}" )
            self.assertRegex( result.stderr, REGEX_ONE_OF )

    def test_010_no_args(self):
        result = Runner.run( [], ENV_EMPTY, RPSL_EMPTY )
        self.assertEqual( result.returncode, EXIT_ARGUMENT_ERROR, f"no arguments exits with {EXIT_ARGUMENT_ERROR}" )
        self.assertRegex( result.stderr, REGEX_ONE_OF )

    def test_020_help(self):
        result = Runner.run( ['--help'], ENV_EMPTY, RPSL_EMPTY )
        self.assertEqual( result.returncode, EXIT_SUCCESS, '--help exits successfully' )

    def test_020_u_and_h(self):
        result = Runner.run( ['-u', IRRD_URL, '-h', 'host'], ENV_EMPTY, RPSL_EMPTY )
        self.assertEqual( result.returncode, EXIT_ARGUMENT_ERROR, f"using both -u and -h exits with {EXIT_ARGUMENT_ERROR}" )
        self.assertRegex( result.stderr, REGEX_NO_H_WITH_U )

    def test_030_empty_input_option(self):
        result = Runner.run( ['-u', IRRD_URL], ENV_EMPTY, RPSL_EMPTY )
        self.assertEqual( result.returncode, EXIT_INPUT_ERROR, f"empty input with -u exits with {EXIT_INPUT_ERROR}" )
        self.assertRegex( result.stderr, REGEX_NO_OBJECTS )

    def test_030_empty_input_env(self):
        result = Runner.run( [], ENV_URL, RPSL_EMPTY )
        self.assertEqual( result.returncode, EXIT_INPUT_ERROR, f"empty input with {ENV_URL} exits with {EXIT_INPUT_ERROR}" )
        result = Runner.run( [], ENV_HOST, RPSL_EMPTY )
        self.assertEqual( result.returncode, EXIT_INPUT_ERROR, f"empty input with {ENV_HOST} exits with {EXIT_INPUT_ERROR}" )
        self.assertRegex( result.stderr, REGEX_NO_OBJECTS )

    def test_030_only_whitespace_input(self):
        result = Runner.run( ['-u', IRRD_URL], ENV_EMPTY, RPSL_WHITESPACE )
        self.assertEqual( result.returncode, EXIT_INPUT_ERROR, f"whitespace only input exits with {EXIT_INPUT_ERROR}" )
        self.assertRegex( result.stderr, REGEX_NO_OBJECTS )

    def test_040_unresovlable_host(self):
        url = UNRESOVABLE_URL
        result = Runner.run( ['-u', url], ENV_EMPTY, RPSL_MINIMAL )
        self.assertEqual( result.returncode, EXIT_NETWORK_ERROR, f"Unresolvable host in {url} exits with {EXIT_NETWORK_ERROR}" )
        self.assertRegex( result.stderr, REGEX_UNRESOLVABLE )

    def test_040_unreachable_host(self):
        url = UNREACHABLE_URL
        result = Runner.run( ['-u', url], ENV_EMPTY, RPSL_MINIMAL )
        self.assertEqual( result.returncode, EXIT_NETWORK_ERROR, f"Unreachable host in {url} with {EXIT_NETWORK_ERROR}" )
        self.assertRegex( result.stderr, REGEX_UNREACHABLE )

    def test_050_non_json_response(self):
        url = BAD_RESPONSE_URL
        result = Runner.run( ['-u', url], ENV_EMPTY, RPSL_MINIMAL )
        self.assertEqual( result.returncode, EXIT_NETWORK_ERROR, f"Bad response URL {url} exits with {EXIT_NETWORK_ERROR}" )
        self.assertRegex( result.stderr, REGEX_BAD_RESPONSE )


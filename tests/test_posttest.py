import pytest
import logging
import time

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.posttest,
    pytest.mark.topology('util'),
    pytest.mark.sanity_check(skip_sanity=True),
    pytest.mark.disable_loganalyzer
]


def test_collect_techsupport(duthosts, enum_dut_hostname):
    duthost = duthosts[enum_dut_hostname]
    """
    A util for collecting techsupport after tests.

    Since nightly test on Jenkins will do a cleanup at the beginning of tests,
    we need a method to save history logs and dumps. This util does the job.
    """
    logger.info("Collecting techsupport since yesterday")
    # Because Jenkins is configured to save artifacts from tests/logs,
    # and this util is mainly designed for running on Jenkins,
    # save path is fixed to logs for now.
    TECHSUPPORT_SAVE_PATH = 'logs/'
    out = duthost.command("generate_dump -s yesterday", module_ignore_errors=True)
    if out['rc'] == 0:
        tar_file = out['stdout_lines'][-1]
        duthost.fetch(src=tar_file, dest=TECHSUPPORT_SAVE_PATH, flat=True)

    assert True


def test_restore_container_autorestart(duthosts, enum_dut_hostname, enable_container_autorestart):
    duthost = duthosts[enum_dut_hostname]
    enable_container_autorestart(duthost)
    # Wait sometime for snmp reloading
    SNMP_RELOADING_TIME = 30
    time.sleep(SNMP_RELOADING_TIME)

def test_recover_rsyslog_rate_limit(duthosts, enum_frontend_dut_hostname):
    duthost = duthosts[enum_frontend_dut_hostname]
    running_dockers = duthost.command("docker ps --format \{\{.Names\}\}")['stdout_lines']
    cmd_enable_rate_limit = r"docker exec -i {} sed -i 's/^#\$SystemLogRateLimit/\$SystemLogRateLimit/g' /etc/rsyslog.conf"
    cmd_reload = r"docker exec -i {} supervisorctl restart rsyslogd"
    for docker_name in running_dockers:
        if duthost.get_facts()['num_asic'] > 1 and docker_name == "database":
            # On linecards, rsyslogd status on global database is not 'RUNNING' and thus it fails
            continue
        cmds = []
        cmds.append(cmd_enable_rate_limit.format(docker_name))
        cmds.append(cmd_reload.format(docker_name))
        duthost.shell_cmds(cmds=cmds)


import pytest
import logging
import json

from tests.common.errors import RunAnsibleModuleFail


@pytest.fixture(scope="module", autouse=True)
def chassis_facts(duthosts):
    """
    Fixture to add some items to host facts from inventory file.
    """
    for a_host in duthosts.nodes:

        if len(duthosts.supervisor_nodes) > 0:
            out = a_host.command("cat /etc/sonic/card_details.json")
            card_details = json.loads(out['stdout'])
            if 'slot_num' in card_details:
                a_host.facts['slot_num'] = card_details['slot_num']


@pytest.fixture(scope="module")
def nbrhosts_facts(nbrhosts):
    nbrhosts_facts = {}
    for a_vm in nbrhosts:
        try:
            vm_facts = nbrhosts[a_vm]['host'].eos_facts()
        except RunAnsibleModuleFail:
            logging.error("VM: %s is down, skipping config fetching.", a_vm)
            continue
        logging.debug("vm facts: {}".format(json.dumps(vm_facts, indent=4)))
        nbrhosts_facts[a_vm] = vm_facts
    return nbrhosts_facts


@pytest.fixture(scope="module")
def all_cfg_facts(duthosts):
    # { 'ixr_vdk_boar10' : [ asic0_results, asic1_results ] }
    #   asic0_results['ansible_facts']
    # result = duthosts.config_facts(source='persistent', asic_index='all')
    # return result
    results = {}
    for node in duthosts.nodes:
        results[node.hostname] = node.config_facts(source='persistent', asic_index='all')
    return results

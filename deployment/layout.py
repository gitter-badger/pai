from kubernetes import client, config
import yaml


def generate_layout(output_file):
    # init client
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # api server url
    api_servers_url = v1.api_client.configuration.host
    # generate dashboard-url
    services = v1.list_service_for_all_namespaces(field_selector="metadata.name=kubernetes-dashboard", pretty=False, timeout_seconds=56, watch=False)
    dashboard_service = services.items[0]
    dashboard_url = "http://{0}:80".format(dashboard_service.spec.cluster_ip)

    # query k8s nodes
    nodes = v1.list_node(pretty=False, timeout_seconds=56, watch=False)
    addressesList = map(lambda node: node.status.addresses, nodes.items)
    machineList = []
    for addresses in addressesList:
        machine = dict()
        machine['machine-type'] = 'GENERIC'
        for address in addresses:
            if address.type == 'InternalIP':
                machine['hostip'] = address.address
            if address.type == 'Hostname':
                machine['hostname'] = address.address
                # TODO nodename == hostname on aks
                machine['nodename'] = address.address
        machineList.append(machine)
    machineList.sort(key=lambda k: k['hostname'])

    # assgin pai-master
    master = machineList[0]
    master['pai-master'] = 'true'
    master['zkid'] = 1

    # assign pai-workers
    workers = machineList[1:] if len(machineList) > 1 else machineList
    for worker in workers:
        worker['pai-worker'] = 'true'

    # the default sku
    machineSku = yaml.load("""
GENERIC:
    mem: 1
    gpu:
        type: generic
        count: 1
    cpu:
        vcore: 1
    os: ubuntu16.04
    """)

    layout = {
        "kubernetes": {
            "api-servers-url": api_servers_url,
            "dashboard-url": dashboard_url
        },
        "machine-sku": machineSku,
        "machine-list": machineList
    }
    # print(yaml.dump(layout, default_flow_style=False))
    with open(output_file, 'w') as outfile:
        yaml.dump(layout, outfile, default_flow_style=False)

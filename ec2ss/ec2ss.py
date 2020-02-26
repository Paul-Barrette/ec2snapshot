import boto3
import botocore
import click

session = boto3.Session(profile_name="ec2snapshot")
ec2 = session.resource("ec2")

@click.group()
def cli():
    """ec2ss manages sanpshots"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option("--project", default=None, help="Only list snapshots for the instance that have the tag 'Project' with the value specified")
def list_volumes(project):
    "Lists the snapshots of EC2 instances for the account"
    instances= get_instances_list(project)
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((i.id, v.id, s.id, s.state, s.progress, s.start_time.strftime("%c"))), end="")
                if(v.encrypted):
                    print(", Encrypted")
                else:
                    print(", Not encrypted")
            else:
                print(i.id + " " + v.id + " There are no snapshots for the volume of this instance.")
    return

@cli.group('volumes')
def volumes():
    """Commands for instances"""

@volumes.command('list')
@click.option("--project", default=None, help="Only list volumes for the instance that have the tag 'Project' with the value specified")
def list_volumes(project):
    "Lists the volumes of EC2 instances for the account"
    instances= get_instances_list(project)
    for i in instances:
        for v in i.volumes.all():
            print(i.state["Name"])
            if i.state["Name"] != "terminated":
                print(", ".join((i.id, v.id, v.state, str(v.size) + "Gib")), end="")
                if(v.encrypted):
                    print(", Encrypted")
                else:
                    print(", Not encrypted")
            else:
                print(i.id + " There are no volumes for this instance. This instance is " + i.state["Name"] + ".")
    return

@cli.group('instances')
def instances():
    """Commands for instances"""

def get_instances_list(project):
    instances = []

    if project:
        print("--------------------------------------------------")
        print("Fetching instances with '" + project + "' as a Project tags" )
        print("--------------------------------------------------")
        filters = [{"Name":"tag:Project", "Values":[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        print("--------------------------------------------------")
        print("Fetching all instances for any value for the Project tags")
        print("--------------------------------------------------")
        instances = ec2.instances.all()
    return instances

@instances.command('snapshot')
@click.option("--project", default=None, help="Only snapshot instances that have the tag 'Project' with the value specified")

def create_instances(project):
    "Create snapshot for EC2 instances"
    instances= get_instances_list(project)
    if len(list(instances)) > 0 and instances:
        for i in instances:
            if i.state["Name"] == "running":
                print("Stopping instance {0}".format(i.id) + ". Please wait...")
                i.stop()
                i.wait_until_stopped()
                for v in i.volumes.all():
                    print("Creating snapshot of volume {0}".format(v.id))
                    v.create_snapshot(Description="Created by the ec2ss.py utility")
                print("Starting back up instance {0}".format(i.id) + ". Please wait...")
                i.start()
                i.wait_until_running()
            else:
                print("No need to stop instance {0}. It is not running".format(i.id))
                for v in i.volumes.all():
                    print("Creating snapshot of volume {0}".format(v.id))
                    v.create_snapshot(Description="Created by the ec2ss.py utility")

    return

@instances.command('list')
@click.option("--project", default=None, help="Only list instances that have the tag 'Project' with the value specified")

def list_instances(project):
    "Lists the EC2 instances for the account"
    instances= get_instances_list(project)
    if len(list(instances)) > 0 and instances:
        for i in instances:
            tags={}
            for t in i.tags:
                tags[t['Key']] = t['Value']
            print(", ".join((
                i.id,
                i.instance_type,
                i.placement["AvailabilityZone"],
                i.state["Name"],
                tags.get('Project', '<No Project>'))),
                end="")
            if(i.public_dns_name):
                print(", " + i.public_dns_name)
            else:
                print(", None (Private Server)")
    else:
        print("There are no instances that are assigned with a Project tag named: '" + project + "'")
    return

@instances.command('stop')
@click.option('--project', default=None, help="Only stop instances for EC2 instances that have the tag 'Project' with the value specified")

def stop_instances(project):
    "Stop EC2 instances"
    instances= get_instances_list(project)
    for i in instances:
        if i.state["Name"] == "running":
            print("Stopping {0} ...".format(i.id))
            try:
                i.stop()
            except botocore.exeptions.ClientError as e:
                print("Could not stop instance {0}.".format(i.id) + str(e))
                continue
        else:
            print("Instance {0} is not stoppable".format(i.id) + ". This instance is " + i.state["Name"] + ".")
    return

@instances.command('start')
@click.option('--project', default=None, help="Only start instances for EC2 instances that have the tag 'Project' with the value specified")

def start_instances(project):
    "Start EC2 instances"
    instances= get_instances_list(project)
    for i in instances:
        if i.state["Name"] == "stopped":
            print("Starting {0} ...".format(i.id))
            i.start()
            try:
                i.start()
            except botocore.exeptions.ClientError as e:
                print("Could not start instance {0}.".format(i.id) + str(e))
                continue
        else:
            print("Instance {0} is not startable".format(i.id) + ". This instance is " + i.state["Name"] + ".")
    return

if __name__ == '__main__':
    cli()

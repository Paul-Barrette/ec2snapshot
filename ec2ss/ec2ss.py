import boto3
import click

session = boto3.Session(profile_name="ec2snapshot")
ec2 = session.resource("ec2")

@click.group()
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
                print(", None(Private Server)")
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
            i.stop()
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
        else:
            print("Instance {0} is not startable".format(i.id) + ". This instance is " + i.state["Name"] + ".")
    return

if __name__ == '__main__':
    instances()

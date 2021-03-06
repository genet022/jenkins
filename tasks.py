from dotenv import load_dotenv
from invoke import task
import yaml

load_dotenv()


@task
def update_deps(c):
    """ Syncs package dependencies
    """
    c.run("pip-compile")


@task
def build_docs(c):
    c.run("cp README.md docs/index.md")
    c.run("ogc --spec maintainer-spec.yml")


@task(pre=[build_docs])
def upload_docs(c):
    c.run("aws s3 sync site/ s3://jenkaas/docs")


@task
def format(c):
    """ Formats py code
    """
    c.run("black .")


@task
def flake8(c):
    """ Runs flake8 against project
    """
    c.run("flake8 --ignore=E501,W503 jobs/integration")


@task(pre=[flake8])
def test(c):
    """ Run unittest suite
    """
    c.run("pytest jobs/**/test_unit*")


@task
def test_jobs(c, conf):
    """ Tests the Jenkins Job Builder definitions
    """
    c.run("jenkins-jobs --conf {} test jobs/.".format(conf))


@task
def update_jobs(c, conf):
    """ Uploads the Jenkins Job Builder definitions
    """
    c.run("jenkins-jobs --conf {} update jobs/. --worker 8".format(conf))


@task
def list_jobs(c, conf):
    """ list the Jenkins Job Builder definitions
    """
    c.run("jenkins-jobs --conf {} list".format(conf))


@task
def delete_jobs(c, conf, pattern):
    """ Delete jobs based on pattern
    """
    out = c.run("jenkins-jobs --conf {} list |grep '{}'".format(conf, pattern))
    for line in out.stdout.splitlines():
        c.run("jenkins-jobs --conf {} delete {}".format(conf, line.strip()))

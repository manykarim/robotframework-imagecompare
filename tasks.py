import pathlib
import subprocess

from invoke import task

from ImageCompare import imagecompare
from ImageCompare import __version__ as VERSION

ROOT = pathlib.Path(__file__).parent.resolve().as_posix()

@task
def atests(context):
    cmd = [
        "coverage",
        "run",
        "--source=ImageCompare",
        "-p",
        "-m",
        "robot",
        "--loglevel=TRACE:DEBUG",
        f"{ROOT}/atest",
    ]
    subprocess.run(" ".join(cmd), shell=True, check=False)

@task(atests)
def tests(context):
    subprocess.run("coverage combine", shell=True, check=False)
    subprocess.run("coverage report", shell=True, check=False)
    subprocess.run("coverage html", shell=True, check=False)

@task
def libdoc(context):
    print(f"Generating libdoc for library version {VERSION}")
    target = f"{ROOT}/docs/imagecompare.html"
    cmd = [
        "python",
        "-m",
        "robot.libdoc",
        "-n ImageCompare",
        f"-v {VERSION}",
        "ImageCompare",
        target,
    ]
    subprocess.run(" ".join(cmd), shell=True, check=False)

@task
def readme(context):
    with open(f"{ROOT}/docs/README.md", "w", encoding="utf-8") as readme:
        doc_string = imagecompare.__doc__
        readme.write(str(doc_string))
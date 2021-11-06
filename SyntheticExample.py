import os
import shutil
import sys
import tempfile
import subprocess
import git
import pandas as pd
from git import Repo

try:
    from javadiff.javadiff.diff import get_commit_diff
except:
    from javadiff.diff import get_commit_diff

ID = 0


def java_by_env_var(env_var):
    return os.path.join(os.environ[env_var], os.path.normpath('bin/java.exe'))


def get_java_exe_by_version(version):
    java_home = list(filter(lambda x: 'java_home' in x.lower(), os.environ.keys()))
    java_home_version = list(filter(lambda x: f'_{version}_' in x.lower(), java_home))
    if java_home_version:
        return java_by_env_var(java_home_version[0])
    if java_home:
        return java_by_env_var('JAVA_HOME')
    return 'java'


def read_commit(repo_path, flag=False):
    if type(repo_path) == type(''):
        repo = git.Repo(repo_path)
    if flag:
        return repo
    df = pd.read_csv("TrainSet/train.csv")
    commits = df["commit"]
    commits_object = []
    for commit in commits[commits_start:commits_end]:
        commits_object.append(repo.commit(commit))
    return commits_object


def apply_diffmin(path_to_dir):
    global ID

    # TODO: uncomment
    file = subprocess.Popen([get_java_exe_by_version(11),
                             "-jar", r"externals/diffmin-1.0-SNAPSHOT-jar-with-dependencies.jar",
                             os.path.join(path_to_dir, f"{ID}.java"), os.path.join(path_to_dir, "after.java")],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8').communicate()[0].split(
        "\n")[3:]

    # file = subprocess.Popen(["java", "-jar", r"externals/diffmin-1.0-SNAPSHOT-jar-with-dependencies.jar",
    #                          os.path.join(path_to_dir, f"{ID}.java"), os.path.join(path_to_dir, "after.java")],
    #                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    #                         encoding='utf8').communicate()[0].split("\n")[3:]

    check_error = [i for i in file if "(Unknown Source)" in i]
    if "Exception in thread" not in file[0] and len(check_error) == 0:
        empty_repo.index.add([os.path.join(f"{ID}.java")])
        empty_repo.index.commit("before")  # parent commit
        print(f"Parent {empty_repo.commit()}")
        empty_repo.git.stash('push')

        open(os.path.join(dir_repo, f"{ID}.java"), "w").writelines(
            [l for l in open(os.path.join(dir_repo, f"after.java")).readlines()])
        empty_repo.git.add([os.path.join(f"{ID}.java")])
        empty_repo.index.commit("after")  # the real after
        print(f"After {empty_repo.commit()}")
        empty_repo.git.stash('push')

        empty_repo.git.checkout(list_commits_repo[-1].parents[0].hexsha)  # change to parent commit
        with open(os.path.join(path_to_dir, f"{ID}.java"), 'w', encoding="utf-8") as f:
            for i in file:
                f.writelines(i)
                f.writelines("\n")
        commit_to_repo()


def commit_to_repo():
    global ID

    empty_repo.git.add([os.path.join(f"{ID}.java")])
    list_commits_repo.append(empty_repo.index.commit("after diffmin"))  # from diffmin commit
    # print(f"After diff {empty_repo.commit()}")
    empty_repo.git.stash('push')
    # print(ID)


def write_file():
    global ID
    for commit in all_commits:
        for parent in commit.parents:
            diff_index = parent.diff(commit)
            for diff in diff_index:
                # if ID > 1:
                #     return
                if diff.a_path.endswith(".java") and not diff.a_path.lower().endswith("test.java"):
                    try:
                        parent_contents = diff.a_blob.data_stream.read().decode('utf-8')
                        current_contents = diff.b_blob.data_stream.read().decode('utf-8')
                        with open(os.path.join(dir_repo, f"{ID}.java"), 'w', encoding="utf-8") as f:
                            f.writelines(parent_contents)
                        with open(os.path.join(dir_repo, "after.java"), 'w', encoding="utf-8") as f:
                            f.writelines(current_contents)
                        apply_diffmin(dir_repo)
                    except Exception as e:
                        print(e)
                        pass
                    finally:
                        ID += 1


if __name__ == '__main__':
    window_size = 3
    ind = int(sys.argv[1])
    commits_start = ind * window_size
    commits_end = commits_start + window_size

    # TODO: uncomment
    # repo_path = r"C:\Users\shirs\Downloads\commons-collections"
    # repo_path = r"C:\Users\shirs\Desktop\JAVA_SECGAN"
    # dir_repo = tempfile.mkdtemp() + "/SyntheticExample"

    repo_path = r"local_repo"
    repo_path = r"local_repo"
    dir_repo = "./SyntheticExample"

    empty_repo = Repo.clone_from("https://github.com/shirshir05/SyntheticExample.git", dir_repo, branch='main')
    empty_repo.remote().pull('main')

    all_commits = read_commit(repo_path, True)
    if type(all_commits) != list:
        all_commits = list(all_commits.iter_commits('HEAD'))

    list_commits_repo = []
    write_file()

    metrics = []
    for commit in list_commits_repo:
        c = get_commit_diff(dir_repo, commit, analyze_diff=True)  # TODO: change to True
        if c:
            metrics.extend(c.get_metrics())
    pd.DataFrame(metrics).to_csv(f'./results/{ind}.csv', index=False)


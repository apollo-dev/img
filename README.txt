
=== Dependencies
1. python3.4
2. git
3. virtualenv and virtualenvwrapper
4. pip

=== initial setup (must be done only once)
1. make a directory where the code will live (eg. ~/code/)
~$ mkdir code

2. go to that directory
~$ cd code

3. clone the repository with git
~$ git clone https://github.com/apollo-dev/img.git

4. create a virtualenv
~$ mkvirtualenv img --python=/usr/local/bin/python3

5. go into the virtualenv
~$ workon img

6. install the requirements
~$ pip install -r reqs.txt

7. setup the database
~$ sh scripts/make_migrations.sh
~$ dm migrate

8. setup the data path
~$ dm setup --path='<THE PATH WHERE THE PROJECTS WILL LIVE>'

READY

=== to run a project
There are four commands to run
1. dm input -> extracts all images from a .lif archive or directory and creates entries for them in the database.
2. dm regions -> allows files form imageJ to be imported describing regions of the environment
3. dm data -> takes in imageJ tracking files and processes the recognition using
4. dm delete -> allows the removal of specific named cells from the output

There are options associated with each one:
1. dm input
	a.

# Apetizer

## concepts

## use

## install

### Installation

Install python 2.7, virtualenv, libpython2.7-dev & postgresql-devel (libpq-dev in Debian/Ubuntu)

In the directory where you have cloned the repo,
create a virtualenv to collect python packages


    virtualenv --no-site-packages .

Enter the virtualenv context


    source bin/activate

Install the required packages


    pip install -r requirements.txt


Create the database:


    python manage.py migrate


Import the instance code and documentation:


    python manage.py apetizer_documentation

Create a superuser:


    python manage.py createsuperuser


Run the server localy:

    python manage.py runserver


# contribute

## fork and get well

what you don't learn in a closed source company context

it's a mater of organisation ... organisation like company, but also like organising your stuff

get it, enhance it, pull it back ...

this looks like very simple ... but how to explain this concept to the untechnical peoples ?
we are not all masters of git ...
we are not all used to github tools

our purpose to help you so

you have the power to make changes,
to this,
to their,
to our !

so here are the easiest ways to help !

-> edit file in github
-> pull the request 

i think this is why we don't see much people explaining this
nobody told me or explained me how to do ... i had to figure it out by myself


creating a pull request from your fork


## make it yours

propose your changes back to the community

creating a pull request from your fork

## <s>do it yourself</s>

let's make it together !





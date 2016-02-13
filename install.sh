#!/bin/bash
echo ' '
echo ' _______  _____  _______ _______ _____ ______ _______  ______'
echo ' |_____| |_____] |______    |      |    ____/ |______ |_____/'
echo ' |     | |       |______    |    __|__ /_____ |______ |    \_'
echo ' '
echo -e '\n\nAutomatic installer\n'                                           

if [[ "$UID" -ne "0" ]];then
	echo 'You must be root to install Apetizer !'
	exit
fi

### BEGIN PROGRAM

INSTALL_DIR='/srv/apetizer'

if [[ -d "$INSTALL_DIR" ]];then
	echo "You already have apetizer installed. You'll need to remove $INSTALL_DIR if you want to install"
	#exit 1
else

    echo 'Installing requirement...'
    
    apt-get update &> /dev/null
    
    hash python &> /dev/null || {
    	echo '+ Installing Python'
    	apt-get install -y python > /dev/null
    }
    
    hash pip &> /dev/null || {
    	echo '+ Installing Python pip'
    	apt-get install -y python-pip > /dev/null
    }
    
    echo 'Cloning Apetizer ...'
    hash git &> /dev/null || {
    	echo '+ Installing Git'
    	apt-get install -y git > /dev/null
    }
    
    git clone https://github.com/biodigitals/apetizer.git "$INSTALL_DIR"
fi

echo 'Installing requirements ...'
pip install -r "$INSTALL_DIR"/requirements.txt

echo -e '\nInstallation complete!\n\n'

echo 'Adding /etc/init.d/apetizer...'

cat > '/etc/init.d/apetizer' <<EOF
#!/bin/bash
# Copyright (c) 2016 Apetizer
# All rights reserved.
#
# Author: Nicolas Danjean
#
# /etc/init.d/apetizer
#
### BEGIN INIT INFO
# Provides: apetizer
# Required-Start: \$local_fs \$network
# Required-Stop: \$local_fs
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Apetizer Start script
### END INIT INFO


WORK_DIR="$INSTALL_DIR"
SCRIPT="main.py"
DAEMON="\$WORK_DIR/bin/python \$WORK_DIR/\$SCRIPT"
PIDFILE="/var/run/apetizer.pid"
USER="root"

function start () {
	echo -n 'Starting server...'
	
	cd \$WORK_DIR
	echo \$WORK_DIR
	
	source bin/activate
	echo "Sourced \$WORK_DIR"
	echo "starting daemon \$DAEMON"
	/sbin/start-stop-daemon --start --pidfile \$PIDFILE \\
		--user \$USER --group \$USER \\
		-b --make-pidfile \\
		--chuid \$USER \\
		--chdir \$WORK_DIR \\
		--exec \$DAEMON
	echo 'done.'
	}

function stop () {
	echo -n 'Stopping server...'
	/sbin/start-stop-daemon --stop --pidfile \$PIDFILE --signal KILL --verbose
	echo 'done.'
}


case "\$1" in
	'start')
		start
		;;
	'stop')
		stop
		;;
	'restart')
		stop
		start
		;;
	*)
		echo 'Usage: /etc/init.d/apetizer {start|stop|restart}'
		exit 0
		;;
esac

exit 0
EOF

chmod +x '/etc/init.d/apetizer'
update-rc.d apetizer defaults &> /dev/null
echo 'Done, Starting ...'
/etc/init.d/apetizer start
echo 'Connect you on http://your-ip-address:80/'

#!/usr/bin/expect -f
ls
spawn ssh-add $HOME/secrets/githubaction-key.pem
expect "Enter passphrase for $HOME/secrets/githubaction-key.pem:"
send "$SSH_KEY_PASSPHRASE";
expect "Identity added: $HOME/secrets/githubaction-key.pem ($HOME/secrets/githubaction-key.pem)"
interact
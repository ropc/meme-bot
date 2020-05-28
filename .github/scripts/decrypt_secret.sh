#!/bin/sh

# Decrypt the file
mkdir $HOME/secrets
# --batch to prevent interactive command
# --yes to assume "yes" for questions
gpg --quiet --batch --yes --decrypt --passphrase="$SSH_KEY_PASSPHRASE" \
--output $HOME/secrets/githubaction-key.pem $GITHUB_WORKSPACE/.github/scripts/githubaction-key.pem.gpg

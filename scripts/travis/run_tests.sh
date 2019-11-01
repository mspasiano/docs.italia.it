if ! [[ "$TOXENV" =~ ^(docs|lint|eslint|migrations|py36) ]];
then
    args="--including-search"
fi
tox -- $args

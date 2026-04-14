PLAYBOOK = main.yml
REQUIREMENTS = requirements.yml

.PHONY: help install run upgrade lint vault-edit vault-rekey

help:
	@echo "Usage:"
	@echo "  make install        Install ansible-galaxy requirements"
	@echo "  make run            Run the full playbook"
	@echo "  make upgrade        Run full playbook with system upgrade"
	@echo "  make lint           Run ansible-lint"
	@echo "  make vault-edit     Edit the vault file"
	@echo "  make vault-rekey    Rekey the vault file"

install:
	# ansible-galaxy install -r $(REQUIREMENTS)

run: install
	ansible-playbook $(PLAYBOOK)

upgrade: install
	ansible-playbook $(PLAYBOOK) --tags all,upgrade

lint:
	ansible-lint $(PLAYBOOK)

vault-edit:
	ansible-vault edit $(FILE)

vault-rekey:
	ansible-vault rekey $(FILE)

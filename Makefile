.PHONY: help
help:
	@echo "available targets -->\n"
	@cat Makefile | grep ".PHONY" | python -c 'import sys; sys.stdout.write("".join(list(map(lambda line: line.replace(".PHONY"+": ", "") if (".PHONY"+": ") in line else "", sys.stdin))))'

.PHONY: clean
clean:
	if git status | grep -q "working tree clean"; then \
		if [ -f "local.cfg" ]; then \
			printf "\n\033[0;31mrefusing to \`make clean\` due existance of \`local.cfg\` !\033[0m\n"; \
			exit 1; \
		else \
			git clean -fdx; \
		fi \
	else \
		git status; \
		printf "\n\033[0;31mrefusing to \`make clean\` due to \`git status\` !\033[0m\n"; \
		exit 1; \
	fi

.PHONY: fixdocker
fixdocker:
	docker-compose down
	docker system prune -f
	-docker kill $$(docker ps -q)

.PHONY: env
env:
	if [ ! -d "./bin" ]; then \
		virtualenv -p python2.7 .; \
		bin/pip install --upgrade pip; \
		bin/pip install -r requirements.txt; \
		make buildout; \
	fi

.PHONY: buildout
buildout: env
	if [ -f "local.cfg" ]; then \
		bin/buildout -c local.cfg; \
	else \
		bin/buildout; \
	fi

.PHONY: docker-compose
docker-compose: env fixdocker
	docker-compose up

.PHONY: fg
fg: env
	bin/instance fg

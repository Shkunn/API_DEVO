push-git:
	git add .
	git commit -m "Auto commit"
	git push

push-heroku:
	heroku container:push web --app api-devo-docker
	heroku container:release web

push: push-git push-heroku

run-local: 
	docker run -it -e PORT=5000 -p 5000:5000 registry.heroku.com/api-devo-docker/web:latest
push-git:
	git add .
	git commit -m "Auto commit"
	git push

push-heroku:
	heroku container:push web --app api-devo-docker
	heroku container:release web

push: push-git push-heroku
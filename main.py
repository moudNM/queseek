from app import app

if __name__ == "__main__":
	app.run(host='127.0.0.1', port=8080, debug =True, use_reloader=True)

# socketio.run(app, host='0.0.0.0', port=5000)
# https://www.youtube.com/watch?v=eayijy9f240
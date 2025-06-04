from flask import Flask, request
import os
import time
import math
import logging
import signal

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

shutting_down = False

def handle_sigterm(signum, frame):
    global shutting_down
    app.logger.info(f"Signal {signal.Signals(signum).name} received, initiating graceful shutdown...")
    shutting_down = True

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

@app.route('/')
def main_route():
    global shutting_down
    if shutting_down:
        app.logger.info("Application is shutting down, request rejected.")
        return "Application is shutting down.", 503

    hostname = os.uname()[1]
    client_ip = request.remote_addr
    cpu_work_iterations = 500000
    app.logger.info(f"Request received on pod {hostname} from {client_ip}. Starting CPU work ({cpu_work_iterations} iterations)...")

    start_time = time.time()
    iterations_completed = 0
    for i in range(cpu_work_iterations):
        if shutting_down:
            app.logger.info(f"Pod {hostname}: Shutdown during CPU work. Exiting loop after {iterations_completed} iterations.")
            break
        _ = math.sqrt(float(i) + 0.001)
        iterations_completed += 1
        if i % (cpu_work_iterations // 5) == 0 and i > 0:
            app.logger.debug(f"Pod {hostname}: CPU work { (i / cpu_work_iterations) * 100 :.0f}% complete.")

    duration = time.time() - start_time
    if shutting_down and iterations_completed < cpu_work_iterations:
         response_message = f"Pod {hostname}: Partial request from {client_ip} due to shutdown. Work interrupted after {duration:.4f}s ({iterations_completed}/{cpu_work_iterations} iter).\n"
    else:
        response_message = f"Pod {hostname}: Processed request from {client_ip} in {duration:.4f}s.\n"
    app.logger.info(f"Pod {hostname} finished request from {client_ip}. Duration: {duration:.4f}s. Iterations: {iterations_completed}.")
    return response_message

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.logger.info(f"Application starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) # debug=False for better signal handling
    app.logger.info("Application has shut down.")

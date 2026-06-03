from flask import Blueprint, request, jsonify
from server.ai import analyze_schedule, suggest_break

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/schedule-analysis', methods=['POST'])
def schedule_analysis():
    data = request.get_json()
    if not data or not data.get('date'):
        return jsonify({'error': 'date is required'}), 400
    try:
        return jsonify(analyze_schedule(data['date']))
    except Exception as e:
        return jsonify({'error': str(e)}), 503


@ai_bp.route('/break-suggestion', methods=['POST'])
def break_suggestion():
    data = request.get_json()
    if not data or not data.get('date'):
        return jsonify({'error': 'date is required'}), 400
    try:
        return jsonify(suggest_break(data['date']))
    except Exception as e:
        return jsonify({'error': str(e)}), 503

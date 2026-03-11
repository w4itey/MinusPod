"""Sponsor routes: /sponsors/* and normalization endpoints."""
import json
import logging
import re

from flask import request

from api import (
    api, log_request, json_response, error_response,
    get_database, get_sponsor_service,
)

logger = logging.getLogger('podcast.api')


# ========== Sponsor Endpoints ==========

@api.route('/sponsors', methods=['GET'])
@log_request
def list_sponsors():
    """List all known sponsors."""
    service = get_sponsor_service()
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    sponsors = service.db.get_known_sponsors(active_only=not include_inactive)

    # Parse JSON fields
    result = []
    for s in sponsors:
        sponsor_data = dict(s)
        # Parse aliases from JSON string
        if isinstance(sponsor_data.get('aliases'), str):
            try:
                sponsor_data['aliases'] = json.loads(sponsor_data['aliases'])
            except json.JSONDecodeError:
                sponsor_data['aliases'] = []
        # Parse common_ctas from JSON string
        if isinstance(sponsor_data.get('common_ctas'), str):
            try:
                sponsor_data['common_ctas'] = json.loads(sponsor_data['common_ctas'])
            except json.JSONDecodeError:
                sponsor_data['common_ctas'] = []
        result.append(sponsor_data)

    return json_response({'sponsors': result})


@api.route('/sponsors', methods=['POST'])
@log_request
def add_sponsor():
    """Add a new sponsor."""
    data = request.get_json()
    if not data or not data.get('name'):
        return error_response('Name is required', 400)

    service = get_sponsor_service()

    # Check if sponsor already exists
    existing = service.db.get_known_sponsor_by_name(data['name'])
    if existing:
        return error_response(f"Sponsor '{data['name']}' already exists", 409)

    sponsor_id = service.add_sponsor(
        name=data['name'],
        aliases=data.get('aliases', []),
        category=data.get('category')
    )

    return json_response({
        'message': 'Sponsor created',
        'id': sponsor_id
    }, 201)


@api.route('/sponsors/<int:sponsor_id>', methods=['GET'])
@log_request
def get_sponsor(sponsor_id):
    """Get a single sponsor by ID."""
    db = get_database()
    sponsor = db.get_known_sponsor_by_id(sponsor_id)

    if not sponsor:
        return error_response('Sponsor not found', 404)

    sponsor_data = dict(sponsor)
    if isinstance(sponsor_data.get('aliases'), str):
        try:
            sponsor_data['aliases'] = json.loads(sponsor_data['aliases'])
        except json.JSONDecodeError:
            sponsor_data['aliases'] = []
    if isinstance(sponsor_data.get('common_ctas'), str):
        try:
            sponsor_data['common_ctas'] = json.loads(sponsor_data['common_ctas'])
        except json.JSONDecodeError:
            sponsor_data['common_ctas'] = []

    return json_response(sponsor_data)


@api.route('/sponsors/<int:sponsor_id>', methods=['PUT'])
@log_request
def update_sponsor(sponsor_id):
    """Update a sponsor."""
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)

    service = get_sponsor_service()

    # Check sponsor exists
    existing = service.db.get_known_sponsor_by_id(sponsor_id)
    if not existing:
        return error_response('Sponsor not found', 404)

    success = service.update_sponsor(sponsor_id, **data)

    if success:
        return json_response({'message': 'Sponsor updated'})
    return error_response('No valid fields to update', 400)


@api.route('/sponsors/<int:sponsor_id>', methods=['DELETE'])
@log_request
def delete_sponsor(sponsor_id):
    """Delete (deactivate) a sponsor."""
    service = get_sponsor_service()

    success = service.delete_sponsor(sponsor_id)

    if success:
        return json_response({'message': 'Sponsor deleted'})
    return error_response('Sponsor not found', 404)


# ========== Normalization Endpoints ==========

@api.route('/sponsors/normalizations', methods=['GET'])
@log_request
def list_normalizations():
    """List all sponsor normalizations."""
    service = get_sponsor_service()
    category = request.args.get('category')
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    normalizations = service.db.get_sponsor_normalizations(
        category=category,
        active_only=not include_inactive
    )

    return json_response({'normalizations': normalizations})


@api.route('/sponsors/normalizations', methods=['POST'])
@log_request
def add_normalization():
    """Add a new normalization."""
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)

    required = ['pattern', 'replacement', 'category']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}", 400)

    if data['category'] not in ('sponsor', 'url', 'number', 'phrase'):
        return error_response("Category must be one of: sponsor, url, number, phrase", 400)

    # Validate regex pattern
    try:
        re.compile(data['pattern'])
    except re.error as e:
        return error_response(f"Invalid regex pattern: {e}", 400)

    service = get_sponsor_service()

    norm_id = service.add_normalization(
        pattern=data['pattern'],
        replacement=data['replacement'],
        category=data['category']
    )

    return json_response({
        'message': 'Normalization created',
        'id': norm_id
    }, 201)


@api.route('/sponsors/normalizations/<int:norm_id>', methods=['PUT'])
@log_request
def update_normalization(norm_id):
    """Update a normalization."""
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)

    # Validate regex pattern if provided
    if 'pattern' in data:
        try:
            re.compile(data['pattern'])
        except re.error as e:
            return error_response(f"Invalid regex pattern: {e}", 400)

    if 'category' in data and data['category'] not in ('sponsor', 'url', 'number', 'phrase'):
        return error_response("Category must be one of: sponsor, url, number, phrase", 400)

    service = get_sponsor_service()
    success = service.update_normalization(norm_id, **data)

    if success:
        return json_response({'message': 'Normalization updated'})
    return error_response('Normalization not found or no valid fields', 404)


@api.route('/sponsors/normalizations/<int:norm_id>', methods=['DELETE'])
@log_request
def delete_normalization(norm_id):
    """Delete (deactivate) a normalization."""
    service = get_sponsor_service()

    success = service.delete_normalization(norm_id)

    if success:
        return json_response({'message': 'Normalization deleted'})
    return error_response('Normalization not found', 404)

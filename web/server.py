#!/usr/bin/env python3
#coding: utf-8

# IMPORTS
from classes.user import User
from classes.user_mh_call import MhCall
from classes.user_partage import Partage
from classes.coterie import Coterie
from classes.coterie_hook import Hook
from classes.being import Being
from classes.being_troll import Troll
from classes.being_troll_private import TrollPrivate
from classes.being_mob import Mob
from classes.being_mob_private import MobPrivate
from classes.tresor import Tresor
from classes.tresor_private import TresorPrivate
from classes.champi import Champi
from classes.champi_private import ChampiPrivate
from classes.maisonnee import Maisonnee
from classes.lieu import Lieu
from classes.event import Event
from classes.event_cdm import cdmEvent
from modules.mh_caller import MhCaller
from modules.sql_helper import unaccent
from functools import wraps
from flask import Flask, url_for, render_template, jsonify, request, make_response, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt, get_jwt_identity
from flask_jwt_extended.view_decorators import _decode_jwt_from_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from sqlalchemy import func, or_, and_, asc, desc
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import OAuthError
import datetime, dateutil.relativedelta, json, math, re, sys, logging, urllib.parse
import modules.globals as sg
import traceback

# WEBAPP DEFINITION
webapp = Flask('SCIZ', static_folder='./web/dist-public/static', template_folder='./web/dist-public/template')
if webapp.debug or webapp.testing or webapp.env != 'production':
    cors = CORS(webapp, resources={r"/api/*": {"origins": "*"}})
jwt = JWTManager()
oauth = OAuth()

# WEBAPP CONFIG
@webapp.before_first_request
def configure():
    # SCIZ startup
    if sg.sciz is None:
        try:
            from sciz import SCIZ
            sciz = SCIZ('confs/sciz_main.yaml', 'INFO')
            sg.logger.info('The bats woke up!')
            sg.logger.info('Starting the web server...')
            sg.logger = logging.getLogger('server')
        except Exception as e:
            print('The bats went sick. Check the log file?', file=sys.stderr)
            if sg.logger is not None:
                sg.logger.exception(e)
            else:
                traceback.print_exc()
            sys.exit(1)
    # Setup
    webapp.config['SECRET_KEY'] = sg.conf[sg.CONF_WEB_SECTION][sg.CONF_WEB_SECRET]
    webapp.config['JWT_SECRET_KEY'] = sg.conf[sg.CONF_WEB_SECTION][sg.CONF_WEB_SECRET]
    webapp.config['JWT_TOKEN_LOCATION'] = 'headers'
    webapp.config['JWT_HEADER_NAME'] = 'Authorization'
    webapp.config['JWT_HEADER_TYPE'] = ''
    webapp.config['JWT_IDENTITY_CLAIM'] = 'identity'
    webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    webapp.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    webapp.config['SESSION_COOKIE_NAME'] = 'session'
    webapp.config['SESSION_COOKIE_SECURE'] = True
    jwt.init_app(webapp)
    oauth.init_app(webapp)
    oauth.register(
        name = 'mh',
        server_metadata_url = sg.conf[sg.CONF_MH_SECTION][sg.CONF_OAUTH_SERVER_METADATA_URL],
        client_id = sg.conf[sg.CONF_MH_SECTION][sg.CONF_OAUTH_CLIENT_ID],
        client_secret = sg.conf[sg.CONF_MH_SECTION][sg.CONF_OAUTH_CLIENT_SECRET],
        client_kwargs = {'scope': sg.conf[sg.CONF_MH_SECTION][sg.CONF_OAUTH_CLIENT_SCOPE]}
    )

@webapp.errorhandler(500)
def internal_error(error):
    sg.db.session.rollback()
    return render_template('index.html')

# SESSION RENEWER
@webapp.before_request
def start_global_session():
    sg.db.session = sg.db.new_session()

@webapp.after_request
def close_global_session(response):
    sg.db.session.close()
    return response

# JWT CONFIG
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    now = datetime.datetime.now()
    if isinstance(identity, User):
        return {
            'hook_type': 'USER',
            'nom': identity.troll.nom,
            'blason_uri': identity.troll.blason_uri
        }
    elif isinstance(identity, Hook):
        return {'hook_type': 'HOOK', 'sub': identity.id, 'type': identity.type}
    else:
        return { 'sub': identity.id }

def jwt_check(view_function):
    @wraps(view_function)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return view_function(*args, **kwargs)
    return wrapper

def user_jwt_check(view_function):
    @wraps(view_function)
    @jwt_required()
    def wrapper(*args, **kwargs):
        jwt_data = _decode_jwt_from_request(locations='headers', fresh=False)[0]
        authorized = jwt_data['hook_type'] == 'USER'
        if not authorized: raise NoAuthorizationError('Non autorisé')
        return view_function(*args, **kwargs)
    return wrapper

def hook_jwt_check(view_function):
    @wraps(view_function)
    @jwt_required()
    def wrapper(*args, **kwargs):
        jwt_data = _decode_jwt_from_request(locations='headers', fresh=False)[0]
        try:
            authorized = jwt_data['hook_type'] == 'HOOK'
        except:
            # Backward compatibility with OLD SCIZ version
            authorized = jwt_data['user_claims']['hook_type'] == 'HOOK'
        if not authorized:
            raise NoAuthorizationError('Non autorisé')
        if sg.db.session.query(Hook).filter(Hook.jwt==request.headers['Authorization']).count() < 1:
            raise NoAuthorizationError('Hook révoqué')
        return view_function(*args, **kwargs)
    return wrapper

# ROUTES DEFINITION

# AUTHENTIFICATION
@webapp.route('/api/login')
def login():
    sg.logger.info("HERE")
    redirect_uri = url_for('authorize', _external=True)
    return oauth.mh.authorize_redirect(redirect_uri)

@webapp.route('/api/login/callback')
def authorize():
    try:
        token = oauth.mh.authorize_access_token()
    except OAuthError as o:
        sg.logger.exception(o)
        return redirect('/?error=1')
    print("test")
    if token is None:
        return redirect('/?error=1')
    userinfo = oauth.mh.userinfo()
    if userinfo is None:
        sg.logger.error('Missing info from MH for logging user: ' + userinfo)
        return redirect('/?error=1')
    # Create all the user in the maisonnee
    ids = list(dict.fromkeys(userinfo['ids'] + [userinfo['sub']]))
    maisonnee_id = sg.db.session.query(Troll.maisonnee_id).filter(Troll.id.in_(ids)).first()[0]
    if maisonnee_id is None:
        maisonnee_id = sg.db.upsert(Maisonnee()).id
    for _id in ids:
        user = sg.db.session.query(User).get(_id)
        if user is None:
            user = User(id = _id)
        user.troll = Troll(id = _id, maisonnee_id = maisonnee_id)
        user = sg.db.upsert(user)
    # Update the current user
    user = sg.db.session.query(User).get(_id)
    user.troll.nom = userinfo['nom']
    user.troll.niv = userinfo['niveau']
    user.troll.race = userinfo['race']
    if userinfo['blason'].startswith('/MH_Blasons/'):
    	userinfo['blason'] = 'https://games.mountyhall.com/' + userinfo['blason']
    user.troll.blason_uri = userinfo['blason'].split('?')[0]
    user.troll.guilde_id = userinfo['guilde']['id'] if userinfo['guilde'] is not None else None
    user = sg.db.upsert(user)
    jwt = create_access_token(identity=user, expires_delta=datetime.timedelta(minutes=user.web_session_duration))
    res = make_response(render_template('index.html'))
    res.set_cookie('sciz_session', jwt, secure=True)
    return res, 200

@webapp.route('/api/login_as/<int:troll_id>', endpoint='login_as', methods=('GET','POST',))
@user_jwt_check
def login_as(troll_id):
    maisonnee_id = sg.db.session.query(Troll.maisonnee_id).filter(Troll.id == get_jwt_identity()).scalar()
    if maisonnee_id is None:
        return jsonify(message='Autorisation requise'), 401
    if sg.db.session.query(Troll).filter(and_(Troll.id == troll_id, Troll.maisonnee_id == maisonnee_id)).count() < 1:
        return jsonify(message='Autorisation requise'), 401
    user = sg.db.session.query(User).get(troll_id)
    jwt = create_access_token(identity=user, expires_delta=datetime.timedelta(minutes=user.web_session_duration))
    res = make_response()
    res.set_cookie('sciz_session', jwt, secure=True)
    return res, 200

# MOBS
@webapp.route('/api/mobs', endpoint='get_mobs_list', methods=('POST',))
@user_jwt_check
def get_mobs_list():
    data = request.get_json()
    if 'search' not in data:
        return jsonify(message='Une erreur est survenue...'), 400
    v = sg.flatten(data.get('search'))
    f = or_(unaccent(cdmEvent.mob_nom).ilike('%' + v + '%'), unaccent(cdmEvent.mob_age).ilike('%' + v + '%'))
    cdms = sg.db.session.query(cdmEvent).distinct(cdmEvent.mob_nom, cdmEvent.mob_age).filter(f).group_by(Event.id, cdmEvent.id, cdmEvent.mob_nom, cdmEvent.mob_age).all()
    l = []
    for cdm in cdms:
        l.append({'nom': cdm.mob_nom + ' [' + cdm.mob_age + ']', 'blason_uri': cdm.mob.blason_uri})
    res = jsonify(l)
    return res, 200

@webapp.route('/api/nbCDM', endpoint='get_nb_cdm', methods=('GET',))
@user_jwt_check
def get_nb_cdm():
    res = jsonify(sg.db.session.query(cdmEvent).count())
    return res, 200

# USER PROFIL
@webapp.route('/api/users/<int:id>', endpoint='get_users_list', methods=('GET',))
@user_jwt_check
def get_users_list(id):
    coterie = sg.db.session.query(Coterie).get(id)
    users = sg.db.session.query(User).all()
    l = []
    for u in users:
        if u.id != get_jwt_identity() and not coterie.has_partage(u.id, False):
            l.append({'id': u.id, 'nom': u.nom, 'blason_uri': u.blason_uri})
    res = jsonify(l)
    return res, 200

@webapp.route('/api/profil', endpoint='get_profil', methods=('GET',))
@user_jwt_check
def get_profil():
    user = sg.db.session.query(User).get(get_jwt_identity())
    res = jsonify(sciz_mail=user.mail, user_mail=user.user_mail,
                  session=user.web_session_duration // 60, pwd_mh=user.mh_api_key,
                  max_sp_dyn=user.max_mh_sp_dynamic, max_sp_sta=user.max_mh_sp_static,
                  count_sp_dyn=user.nb_calls_today('Dynamique'), count_sp_sta=user.nb_calls_today('Statique'))
    return res, 200

@webapp.route('/api/maisonnee', endpoint='get_maisonnee', methods=('GET',))
@user_jwt_check
def get_maisonnee():
    user = sg.db.session.query(User).get(get_jwt_identity())
    maisonnee = sg.db.session.query(Troll).filter(and_(Troll.maisonnee_id == user.troll.maisonnee_id, Troll.id != user.id)).all()
    trolls = []
    for troll in maisonnee:
        trolls.append({'id': troll.id, 'nom': troll.nom, 'blason_uri': troll.blason_uri})
    return jsonify({'maisonnee': trolls}), 200


@webapp.route('/api/profil', endpoint='set_profil', methods=('POST',))
@user_jwt_check
def set_profil():
    data = request.get_json()
    user = sg.db.session.query(User).get(get_jwt_identity())
    user = user.update(**data)
    if user is None:
        return jsonify(message='Une erreur est survenue...'), 400
    return jsonify(message='Profil sauvegardé !'), 200

@webapp.route('/api/profil', endpoint='delete_profil', methods=('DELETE',))
@user_jwt_check
def delete_profil():
    user = sg.db.session.query(User).get(get_jwt_identity())
    # If the only admin of a group delete its account then everybody becomes admin
    # If there is nobody with an active share, then the group is deleted
    for partage in user.partages:
        if len(partage.coterie.partages_actifs) < 1:
            sg.db.delete(partage.coterie)
        if partage.coterie.has_partage(user.id, True) and len(partage.coterie.partages_admins) <= 1:
            for partage_user in partage.coterie.partages_utilisateurs:
                partage_user.admin = True
                sg.db.upsert(partage_user)
    sg.db.delete(user)
    return jsonify(message='Profil supprimé !'), 200

@webapp.route('/api/calls/<int:page>', endpoint='get_mh_calls', methods=('GET',))
@user_jwt_check
def get_mh_calls(page):
    total_calls = sg.db.session.query(MhCall).filter(MhCall.user_id == get_jwt_identity()).count()
    calls = sg.db.session.query(MhCall).filter(MhCall.user_id == get_jwt_identity()).order_by(MhCall.time.desc()).offset(min(total_calls, 10 * (page - 1))).limit(10).all()
    return jsonify(total=total_calls, calls=[sg.row2dict(c) for c in calls]), 200

# GROUPS
@webapp.route('/api/groups/<path:path>', endpoint='get_coteries', methods=('GET',))
@webapp.route('/api/groups', endpoint='get_coteries', defaults={'path': ''}, methods=('GET',))
@user_jwt_check
def get_coteries(path):
    user = sg.db.session.query(User).get(get_jwt_identity())
    # Shares
    partage_perso = user.partage_perso
    partages_actifs = user.partages_actifs
    partages_invitations = user.partages_invitations if 'withinvites' in path else []
    # Groups
    coterie_perso = sg.row2dict(partage_perso.coterie)
    coteries = [sg.row2dict(p.coterie) for p in partages_actifs]
    invitations = [sg.row2dict(p.coterie) for p in partages_invitations]
    # Add MP/PX link and hooks if admin ans asked for
    for p, c in zip([partage_perso] + partages_actifs + partages_invitations, [coterie_perso] + coteries + invitations):
        c['mp_link'] = p.coterie.mp_link
        c['px_link'] = p.coterie.px_link
        if 'withhooks' in path:
            c['hooks'] = [sg.row2dict(h) for h in p.coterie.hooks]
    # Result
    return jsonify(coterie_perso=coterie_perso, coteries=coteries, invitations=invitations), 200

@webapp.route('/api/group/<int:id>', endpoint='get_coterie', methods=('GET',))
@user_jwt_check
def get_coterie(id):
    coterie = sg.db.session.query(Coterie).get(id)
    c = sg.row2dict(coterie)
    c['px_link'] = coterie.px_link
    c['mp_link'] = coterie.mp_link
    if coterie.has_partage(get_jwt_identity(), False):
        return jsonify(coterie=c), 200
    elif coterie.has_partage(get_jwt_identity(), True):
        return jsonify(coterie=c, hooks=sg.row2dict(coterie.hooks)), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/group/<int:id>', endpoint='set_coterie', methods=('POST',))
@user_jwt_check
def set_coterie(id):
    data = request.get_json()
    coterie = sg.db.session.query(Coterie).get(id)
    coterie.update(get_jwt_identity(), **data) # Admin check is done in routine
    return jsonify(message='Coterie mise à jour'), 200

@webapp.route('/api/group/<int:id>', endpoint='delete_coterie', methods=('DELETE',))
@user_jwt_check
def delete_coterie(id):
    coterie = sg.db.session.query(Coterie).get(id)
    if coterie.has_partage(get_jwt_identity(), True):
        sg.db.delete(coterie)
        return jsonify(message='Coterie supprimée !'), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/share/invite/<int:id>', endpoint='accept_or_refuse_invite', methods=('DELETE', 'POST'))
@user_jwt_check
def accept_or_refuse_invite(id):
    data = request.get_json()
    coterie = sg.db.session.query(Coterie).get(id)
    if coterie.has_pending_partage(get_jwt_identity()):
        now = datetime.datetime.now()
        partage = sg.db.session.query(Partage).filter(Partage.coterie_id==id, Partage.user_id==get_jwt_identity()).order_by(desc(Partage.id)).first()
        if request.method == 'POST':
            partage.pending = False
            partage.start = now
            partage.sharingEvents = data['sharingEvents']
            partage.sharingProfile = data['sharingProfile']
            partage.sharingView = data['sharingView']
            message = 'Invitation acceptée'
        else:
            partage.end = now
            message = 'Invitation déclinée'
        sg.db.upsert(partage)
        return jsonify(message=message), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/group/create', endpoint='create_coterie', methods=('POST',))
@user_jwt_check
def create_coterie():
    data = request.get_json()
    Coterie.create(get_jwt_identity(), data['nom'], data['blason_uri'], data['desc'])
    return jsonify(message='Coterie créée'), 200

@webapp.route('/api/shares/<int:id>', endpoint='get_partages', methods=('GET',))
@user_jwt_check
def get_partages(id):
    coterie = sg.db.session.query(Coterie).get(id)
    if coterie.has_partage(get_jwt_identity()) or coterie.has_pending_partage(get_jwt_identity()):
        return jsonify(admins=[{'partage': sg.row2dict(p), 'nom': p.user.nom, 'blason_uri': p.user.blason_uri} for p in coterie.partages_admins],
                       users=[{'partage': sg.row2dict(p), 'nom': p.user.nom, 'blason_uri': p.user.blason_uri} for p in coterie.partages_utilisateurs],
                       pending=[{'partage': sg.row2dict(p), 'nom': p.user.nom, 'blason_uri': p.user.blason_uri} for p in coterie.partages_invitations]), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/shares/<int:id>', endpoint='delete_partage', methods=('DELETE',))
@user_jwt_check
def delete_partage(id):
    coterie = sg.db.session.query(Coterie).get(id)
    if coterie.has_partage(get_jwt_identity(), False) and not (coterie.has_partage(get_jwt_identity(), True) and len(coterie.partages_admins) <= 1):
        now = datetime.datetime.now()
        partage = sg.db.session.query(Partage).filter(Partage.coterie_id==id, Partage.user_id==get_jwt_identity()).order_by(desc(Partage.id)).first()
        partage.end = now
        sg.db.upsert(partage)
        return jsonify(message='Partage supprimé'), 200
    return jsonify(message='Partage non supprimé'), 400

# EVENTS
@webapp.route('/api/events/<int:coterie_id>/<int:limit>/<int:offset>/<int:last_time>', endpoint='get_user_events', methods=('GET',))
@webapp.route('/api/events/<int:coterie_id>/<int:limit>/<int:offset>/<int:last_time>/revert', endpoint='get_user_events', methods=('GET',))
@user_jwt_check
def get_user_events(coterie_id, limit, offset, last_time):
    coterie = sg.db.session.query(Coterie).get(coterie_id)
    if coterie is not None and coterie.has_partage(get_jwt_identity(), False):
        return jsonify(events=coterie.get_events(min(limit, 100), offset, abs(last_time), 'revert' in request.url_rule.rule)), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/events/<int:event_id>', endpoint='delete_user_event', methods=('DELETE',))
@user_jwt_check
def delete_user_event(event_id):
    event = sg.db.new_session().query(Event).get(event_id)
    user = sg.db.session.query(User).get(get_jwt_identity())
    if event is not None and user is not None and event.owner_id == user.id:
        for p in user.partages:
            for h in p.coterie.hooks:
                if h.last_event_id == event.id:
                    h.last_event_id = sg.db.session.query(Event.id).filter(Event.id < h.last_event_id).order_by(Event.id.desc()).first()
                    sg.db.upsert(h)
        sg.db.delete(event)
        return jsonify(message='Événement supprimé !'), 200
    return jsonify(message='Autorisation requise'), 401

# HOOKS
@webapp.route('/api/hook/renew/<int:id>', endpoint='renew', methods=('POST',))
@user_jwt_check
def renew(id):
    hook = sg.db.session.query(Hook).get(id)
    if hook.coterie.has_partage(get_jwt_identity(), True) or hook.jwt is None:
        hook.jwt = create_access_token(identity=hook, expires_delta=False)
        sg.db.upsert(hook)
        return jsonify(message='Hook renouvelé'), 200
    return jsonify(message='Autorisation requise'), 401

# HOOK REQUESTER (TO BE DELETED WITH THE REQUESTER)
@webapp.route('/api/hook/request', endpoint='make_hook_request', methods=('POST',))
@hook_jwt_check
def make_hook_request():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        data = request.get_json()
        if 'req' not in data:
            return jsonify(message='Une erreur est survenue...'), 400
        res = sg.req.request(hook.coterie, data.get('req'))
        return jsonify(message=res), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/user/request', endpoint='make_user_request', methods=('POST',))
@user_jwt_check
def make_user_request():
    user = sg.db.session.query(User).get(get_jwt_identity())
    data = request.get_json()
    if 'req' not in data:
        return jsonify(message='Une erreur est survenue...'), 400
    res = sg.req.request(user, data.get('req'))
    return jsonify(message=res), 200

# HOOKS DATA
@webapp.route('/api/hook/events', endpoint='get_hook_events', methods=('GET',))
@hook_jwt_check
def get_hook_events():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        return jsonify(events=hook.trigger()), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/events/<int:being_id>/<int:start_time>/<int:end_time>', endpoint='get_hook_events_for', methods=('GET',))
@hook_jwt_check
def get_hook_events_for(being_id, start_time, end_time):
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        return jsonify(events=hook.get_events_for(being_id, start_time, end_time)), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/treasures', endpoint='get_hook_treasures_for', methods=('POST',))
@hook_jwt_check
def get_hook_treasures_for():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        data = request.get_json()
        if 'ids' not in data or not all(i.isdigit() for i in data.get('ids')):
            return jsonify(message='Une erreur est survenue...'), 400
        return jsonify(treasures=hook.get_treasures_for(data.get('ids'))), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/trolls', endpoint='get_hook_trolls_for', methods=('POST',))
@hook_jwt_check
def get_hook_trolls_for():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        return jsonify(trolls=hook.get_trolls_for()), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/bestiaire', endpoint='get_bestiaire', methods=('POST',))
@jwt_check
def get_bestiaire():
    data = request.get_json()
    if 'name' not in data or 'age' not in data:
        return jsonify(message='Une erreur est survenue...'), 400
    return jsonify(bestiaire=sg.req.bestiaire(data.get('name'), data.get('age'))), 200

@webapp.route('/api/bestiaire/check', endpoint='bestiaire_check', methods=('POST',))
@jwt_check
def bestiaire_check():
    data = request.get_json()
    if 'mobs' not in data:
        return jsonify(message='Une erreur est survenue...'), 400
    return jsonify(bestiaire=sg.req.bestiaire_check(data.get('mobs'))), 200


@webapp.route('/api/hook/traps', endpoint='get_hook_traps', methods=('POST',))
@hook_jwt_check
def get_hook_traps():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        data = request.get_json()
        if any(a not in data for a in ['pos_x', 'pos_y', 'pos_n', 'view_h', 'view_v']):
            return jsonify(message='Une erreur est survenue...'), 400
        return jsonify(traps=hook.get_traps_for(data.get('pos_x'), data.get('pos_y'), data.get('pos_n'), data.get('view_h'), data.get('view_v'))), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/portals', endpoint='get_hook_portals', methods=('POST',))
@hook_jwt_check
def get_hook_portals():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        data = request.get_json()
        if 'ids' not in data or not all(i.isdigit() for i in data.get('ids')):
            return jsonify(message='Une erreur est survenue...'), 400
        return jsonify(portals=hook.get_portals_for(data.get('ids'))), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/mushrooms', methods=('POST',))
@hook_jwt_check
def get_hook_mushrooms_for():
    hook = sg.db.session.query(Hook).get(get_jwt_identity())
    if hook is not None:
        data = request.get_json()
        if 'ids' not in data:
            return jsonify(message='Une erreur est survenue...'), 400
        return jsonify(mushrooms=hook.get_mushrooms_for(data.get('ids'))), 200
    return jsonify(message='Autorisation requise'), 401

# HOOK FORMAT
@webapp.route('/api/hook/format/<int:hook_id>', endpoint='get_hook_format', methods=('GET',))
@user_jwt_check
def get_hook_format(hook_id):
    hook = sg.db.session.query(Hook).get(hook_id)
    if hook is not None and hook.coterie.has_partage(get_jwt_identity(), True):
        format = Hook.format2ui(hook.format) if hook.format is not None else Hook.format2ui(sg.format)
        return jsonify(format=json.dumps(format)), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/format/<int:hook_id>', endpoint='set_hook_format', methods=('POST',))
@user_jwt_check
def set_hook_format(hook_id):
    hook = sg.db.session.query(Hook).get(hook_id)
    if hook is not None and hook.coterie.has_partage(get_jwt_identity(), True):
        data = request.get_json()
        hook = hook.update_format(**data)
        if hook is None:
            return jsonify(message='Une erreur est survenue...'), 400
        return jsonify(message='Format sauvegardé !'), 200
    return jsonify(message='Autorisation requise'), 401

@webapp.route('/api/hook/format/<int:hook_id>', endpoint='reset_hook_format', methods=('DELETE',))
@user_jwt_check
def reset_hook_format(hook_id):
    hook = sg.db.session.query(Hook).get(hook_id)
    if hook is not None and hook.coterie.has_partage(get_jwt_identity(), True):
        hook.format = sg.format
        sg.db.upsert(hook)
        return jsonify(message='Configuration réinitialisée'), 200
    return jsonify(message='Autorisation requise'), 401

# MH CALL
@webapp.route('/api/mh_sp_call/<string:script>', endpoint='mh_sp_call', methods=('POST',))
@user_jwt_check
def mh_sp_call(script):
    # Sanity check
    user = sg.db.session.query(User).get(get_jwt_identity())
    type = 'Dynamique' if script in ['profil4', 'vue2'] else None
    #type = 'Statique' if script in [''] else type
    if user is None or type is None:
        return jsonify(message='Une erreur est survenue...'), 400
    # Limits check
    if type == 'Dynamique' and user.nb_calls_today('Dynamique') >= 24:
        return jsonify(message='Maximum de 24 appels aux scripts dynamiques par jour atteint...'), 401
    if type == 'Statique' and user.nb_calls_today('Statique') >= 12:
        return jsonify(message='Maximum de 12 appels aux scripts statiques par jour atteint...'), 401
    # Actual call
    if sg.mc.call(user, [script], False, True):
        return jsonify(message='Appel a %s effectué !' % (script,)), 200
    return jsonify(message='Une erreur est survenue...'), 400


# DEFAULT ROUTE (redirect to VueJS client)
@webapp.route('/', defaults={'path': ''})
@webapp.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')

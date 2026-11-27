const path = require('path');
const request = require('request');

//const SCIZ_URL_BASE = 'http://192.168.0.1:8080/api/hook'
const SCIZ_URL_BASE = 'https://www.sciz.fr/api/hook'
const SCIZ_URL_REQUEST = SCIZ_URL_BASE + '/request'

var db;
var ws;
var bots;

/*
 * Plugin init
 */

exports.name = "sciz";

exports.provider = {
	key: "sciz",
	command: "sciz",
	botName: "SCIZ-Bot",
	botAvatar: {src:'url', key:'https://i.imgur.com/sfd9VyY.png'},
	botInfo: {location: 'Quelque part entre un Trõll et son Zhumain',
		lang: 'fr',
		description: "Je suis une chauve-souris !" },
	help: "Permet d'interagir avec SCIZ",
	detailedHelp: "#lang-md"
								+ "\n * `!!sciz [help|$cli]` requête le guichet SCIZ associée a cette salle"
								+ "\n * `!!sciz unregister` supprime le hook associé à la salle"
								+ "\n * `!!sciz register $jwt` enregistre un hook pour cette salle"
}

const providers = [exports.provider];

async function initProvider(con, p){
	var bot = await con.getBot(p.botName);
	p.bot = bot;
	if (p.botAvatar.src !== bot.avatarsrc || p.botAvatar.key !== bot.avatarkey) {
		bot.avatarsrc = p.botAvatar.src;
		bot.avatarkey = p.botAvatar.key;
		await con.updateUser(bot);
	}
	var info = await con.getUserInfo(bot.id);
	if (info.description !== p.botInfo.description) {
		await con.updateUserInfo(bot.id, p.botInfo);
	}
	bots.register(bot);
}

exports.init = function(miaou){
	db = miaou.db;
	ws = miaou.lib("ws");
	bots = miaou.lib("bots");
	miaou.requestTag({
		name: "MountyHall",
		description:
			"https://games.mountyhall.com/mountyhall/Images/Troll_accueil_1.jpg\n"
			+ "*[MountyHall](https://www.mountyhall.com) est un jeu de rôles et d'aventures"
			+ " en ligne permettant aux participants d'incarner un Troll en quête d'aventures. "
			+ "Le jeu se déroule en tour-par-tour d'une durée de 12 heures durant lesquelles"
			+ " les joueurs peuvent faire agir leur Troll en dépensant jusqu'à 6 Points d'Actions.*\n"
			+ "Donner ce tag à une salle Miaou apporte de nombreuses fonctions liées au jeu MountyHall."
	});
	return db.upgrade(exports.name, path.resolve(__dirname, 'sql'))
		.then(function(){
			return db.do(async function(con){
				for (var p of providers) {
					await initProvider(con, p);
				}
			});
		});
}

/*
 * Route
 */

exports.registerRoutes = function(map){
	providers.forEach(function(p){
		var route = "/" + p.key + "-webhook";
		require('../../libs/anti-csrf.js').whitelist(route);
		map('post', route, (req, res) => scizCalling(p, req, res), true, true);
	});
}

function scizCalling(p, req, res){
	var	jwt = req.headers['authorization'];
	if (!jwt || !req.body) {
		return res.status(400).json({message: 'Bad request'});
	}
	res.send('');
	return db.do(async function(con){
		var row = await con.queryOptionalRow(
			"SELECT room FROM sciz WHERE jwt = $1",
			[jwt],
			"sciz / get room"
		);
		if (row && row.room && req.body && req.body.events) {
			var events = JSON.parse(req.body.events);
			for (var i = 0; i < events.length; i++) {
				if (events[i].message) {
					ws.botMessage(p.bot, row.room, events[i].message);
				}
			}
		}
	});
}

/*
 * Commands
 */

exports.registerCommands = function(cb){
	providers.forEach(function(p){
		cb({
			name: p.command,
			fun: ct => onCommand.call(this, ct, p),
			help: p.help,
			detailedHelp: p.detailedHelp
		});
	});
}

function onCommand(ct, p){
	var m;
	if ((m = ct.args.match(/^register\s+([^\s]+)/))) {
		ct.silent = true;
		ct.nostore = true;
		ct.shoe.checkAuth("admin");
		ws.botMessage(p.bot, ct.shoe.room.id, "Hook SCIZ enregistré pour cette salle");
		return registerRoom.call(this, ct, p, m[1]);
	} else if ((m = ct.args.match(/^unregister/))) {
		ct.shoe.checkAuth("admin");
		ws.botMessage(p.bot, ct.shoe.room.id, "Hook SCIZ supprimé pour cette salle");
		return unregisterRoom.call(this, ct, p);
	} else {
		ct.shoe.checkAuth("write");
		if (!ct.args || ct.args === 'help') {
			ws.botMessage(p.bot, ct.shoe.room.id, "Une chauve-souris vous emmène vers"
				+ " [Mountypedia](http://mountypedia.mountyhall.com/Outils/SCIZ)");
			return;
		}
		return requestSCIZ.call(this, ct, p, ct.args);
	}
}

function registerRoom(ct, p, jwt){
	return db.do(function(con){
		return con.execute(
			"INSERT INTO sciz (room, jwt) VALUES ($1, $2)"
			+ "ON CONFLICT (room) DO UPDATE SET jwt = $2;",
			[ct.shoe.room.id, jwt],
			"sciz / insert or update hook"
		);
	});
}

function unregisterRoom(ct, p){
	return db.do(function(con){
		return con.execute(
			"DELETE FROM sciz WHERE room = $1;",
			[ct.shoe.room.id],
			"sciz / delete hook"
		);
	});
}

function requestSCIZ(ct, p, args){
	/* N.B: args check done SCIZ side */
	return db.do(async function(con){
		var row = await con.queryOptionalRow(
			"SELECT jwt FROM sciz WHERE room = $1",
			[ct.shoe.room.id],
			"sciz / get hook"
		);
		if (!row || !row.jwt) {
			ws.botMessage(p.bot, ct.shoe.room.id, 'Aucun hook SCIZ n\'est enregistré pour cette salle `!!help !!'
				+ p.command + '`');
			return;
		}
		var options = {
			method: 'POST',
			url: SCIZ_URL_REQUEST,
			headers: {
				'Authorization': row.jwt
			},
			json: {'req': args}
		};
		request(options, function(error, response, body){
			if (body && !error && response.statusCode === 200 && body.message) {
				var l = body.message.length
				for (var i = 0; i < l; i++) {
					var m = body.message[i];
					if (i < l - 1) {
						m += "\n-\n";
					}
					ws.botMessage(p.bot, ct.shoe.room.id, m);
				}
			} else {
				ws.botMessage(p.bot, ct.shoe.room.id,
					'SCIZ est inaccessible ou le hook enregistré est invalide `!!help !!'
					+ p.command + '`' + response + body + error);
			}
		});
	});
}


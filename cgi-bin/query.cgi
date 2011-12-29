#!/usr/bin/env python

import cgitb
cgitb.enable()

import sys
import sqlite3
import cgi

try:
	import json
except ImportError:
	import simplejson as json

# action=index

# action=albums [genre=...] [artist=...]
# action=artists [genre=...]
# action=genres
# action=songs (album=... | artist=...)

# action=album name=...
# action=artist name=...
# action=song album=... number=...

# [action=embed] url=... [maxwidth=...] [maxheight=...]

actions = {}
def action(func):
	actions[func.func_name] = func
	return func

def rows_to_dicts(cur,rows):
	return [row_to_dict(cur,row) for row in rows]

def row_to_dict(cur,row):
	return dict((column[0], row[i]) for i, column in enumerate(cur.description))

@action
def index(cur,params):
	rv = {}
	cur.execute('select albumname, artist, sku from albums order by albumname, artist')
	rv['albums'] = rows_to_dicts(cur,cur.fetchall())
	cur.execute('select artist, homepage from artists order by artist')
	rv['artists'] = rows_to_dicts(cur,cur.fetchall())
	cur.execute('select distinct genre from genres order by genre')
	rv['genres'] = genres = []
	for genre_row in cur.fetchall():
		cur.execute(
			'select albumname from genres where genre = ? order by albumname', 
			genre_row)
		genres.append({
			'genre': genre_row[0],
			'albums': [album_row[0] for album_row in cur.fetchall()]
		})
	return rv

@action
def albums(cur,params):
	sql = ['select albums.albumname, albums.artist, albums.sku from albums']
	where = []
	args = []

	if 'genre' in params:
		genre = params.getvalue('genre')
		sql.append(' inner join genres on genres.albumname = albums.albumname ')
		where.append('genres.genre = ?')
		args.append(genre)

	if 'artist' in params:
		artist = params.getvalue('artist')
		where.append('albums.artist = ?')
		args.append(artist)

	if where:
		sql.append(' where ')
		sql.append(' and '.join(where))

	sql.append(' order by albums.albumname, albums.artist')
	cur.execute(''.join(sql),args)
	return rows_to_dicts(cur,cur.fetchall())

@action
def artists(cur,params):
	sql = ['select artists.artist, artists.homepage from artists']
	where = []
	args = []

	if 'genre' in params:
		genre = params.getvalue('genre')
		sql.append(
			' inner join albums on artists.artist = albums.artist '
			' inner join genre on genres.albumname = albums.albumname ')
		where.append('genres.genre = ?')
		args.append(genre)

	sql.append(' order by artists.artist')
	cur.execute(''.join(sql),args)
	return rows_to_dicts(cur,cur.fetchall())

@action
def genres(cur,params):
	cur.execute('select distinct genre from genres order by genre')
	return [row[0] for row in cur.fetchall()]

@action
def songs(cur,params):
	if 'album' in params:
		where = 'albums.albumname = ?'
		args = [params.getvalue('album')]
	else:
		where = 'albums.artist = ?'
		args = [params.getvalue('artist')]

	cur.execute(
		'select songs.number, songs.desc, songs.duration, songs.albumname, songs.mp3, '
		'albums.artist from songs inner join albums on songs.albumname = albums.albumname '
		'where '+where, args)

	return rows_to_dicts(cur,cur.fetchall())

@action
def album(cur,params):
	args = [params.getvalue('name')]
	cur.execute(
		'select albumname, artist, also, description, sku, '
		'launchdate, itunes from albums where albumname = ?',
		args)
	album = cur.fetchone()
	if not album:
		return None
	album = row_to_dict(cur,album)
	cur.execute(
		'select number, desc, duration, mp3 from songs where albumname = ? order by number',
		args)
	album['songs'] = rows_to_dicts(cur,cur.fetchall())
#	cur.execute(
#		'select distinct genre from genres where albumname = ? order by genre',
#		args)
#	album['genres'] = [row[0] for row in cur.fetchall()]
	return album

@action
def artist(cur,params):
	args = [params.getvalue('name')]
	cur.execute(
		'select artist, description, homepage, city, state, '
		'country, bio, bandphoto from artists where artist = ?',
		args)
	artist = cur.fetchone()
	if not artist:
		return None
	artist = row_to_dict(cur,artist)
#	cur.execute('select albumname from albums where artist = ? order by albumname', args)
#	artist['albums'] = rows_to_dicts(cur,cur.fetchall())
	return artist

@action
def song(cur,params):
	args = [params.getvalue('album'), int(params.getvalue('number'),10)]
	cur.execute(
		'select songs.number, songs.desc, songs.duration, songs.albumname, songs.mp3, '
		'albums.artist from songs inner join albums on songs.albumname = albums.albumname '
		'where songs.albumname = ? and songs.number = ?', args)
	song = cur.fetchone()
	if not song:
		return None
	return row_to_dict(cur,song)

@action
def embed(cur,params):
	import urllib, re

	if 'maxwidth' in params:
		width = int(params.getvalue('maxwidth'),10)
	else:
		width = 400

	if 'maxheigth' in params:
		height = int(params.getvalue('maxheigth'),10)
	else:
		height = 300

	m = re.match('^https?://magnatune\.com/artists/albums/([^/]+)', params.getvalue('url'))

	if not m:
		# TODO: correct error status
		return None
	
	sku = m.group(1)

	cur.execute('select albumname, artists.artist, artists.homepage from albums inner join artists on albums.artist = artists.artist where sku = ?', [sku])
	row = cur.fetchone()
	if not row:
		# TODO: correct error status
		return None

	album    = row[0]
	artist   = row[1]
	homepage = row[2]

	large=True
	autoplay=False
	if large:
		if width  <  150: width  =  150
		if width  >  600: width  =  600
		if height <  140: height =  140
		if height > 1000: height = 1000

		if width > 207:
			logo = "<a href=\"http://magnatune.com\"><img src=\"http://he3.magnatune.com/images/magnatune.gif\" border=\"0\"/></a><br/>"
		else:
			logo = ""

		player = "http://embed.magnatune.com/img/magnatune_player_embedded.swf"
	else:
		if width  < 100: width  = 100
		if width  > 600: width  = 600
		if height <  15: height =  15
		if height >  15: height =  15

		logo = ""
		player = "http://embed.magnatune.com/img/magnatune_player_embedded_single.swf"

	if autoplay:
		autoplay = 'true'
	else:
		autoplay = ''

	embedtempl = """\
#LOGO#
<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://fpdownload.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=7,0,0,0" width="#WIDTH#" height="#HEIGHT#" >
	<param name="allowScriptAccess" value="sameDomain"/>
	<param name="movie" value="#PLAYER#?playlist_url=http://embed.magnatune.com/artists/albums/#ALBUM_SKU#/hifi.xspf&autoload=true&autoplay=#AUTOPLAY#&playlist_title=#PLAYLIST_TITLE#"/>
	<param name="quality" value="high"/>
	<param name="bgcolor" value="#E6E6E6"/>
	<embed src="#PLAYER#?playlist_url=http://embed.magnatune.com/artists/albums/#ALBUM_SKU#/hifi.xspf&autoload=true&autoplay=#AUTOPLAY#&playlist_title=#PLAYLIST_TITLE#" quality="high" bgcolor="#E6E6E6" name="xspf_player" allowscriptaccess="sameDomain" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" align="center" height="#HEIGHT#" width="#WIDTH#"></embed>
</object><br/>
<span style="font-face: Verdana, Arial, utopia, Sans-serif; font-size: 1em; color: #000000">
	<a href="http://magnatune.com/artists/albums/#ALBUM_SKU#"><b>#ALBUM_NAME#</b></a> by <a href="http://magnatune.com/artists/#ARTIST_HOMEPAGE#"><b>#ARTIST_NAME#</b></a>
</span>
"""
	html = (embedtempl
		.replace('#WIDTH#', str(width))
		.replace('#HEIGHT#', str(height))
		.replace('#AUTOPLAY#', autoplay)
		.replace('#PLAYER#', player)
		.replace('#LOGO#', logo)
		.replace('#ALBUM_SKU#',sku)
		.replace('#ALBUM_NAME#',cgi.escape(album).encode('ascii','xmlcharrefreplace'))
		.replace('#ARTIST_NAME#',cgi.escape(artist).encode('ascii','xmlcharrefreplace'))
		.replace('#ARTIST_HOMEPAGE#',homepage)
		.replace('#PLAYLIST_TITLE#',urllib.quote(album+' - '+artist)))

	return {
		"version": "1.0",
		"type": "rich",
		"title": album,
		"author_name": artist,
		"author_url": "http://magnatune.com/artists/"+homepage,
		"provider_name": "Magnatune",
		"provider_url": "http://magnatune.com/",
		"thumbnail_url": "http://he3.magnatune.com/music/%s/%s/cover_600.jpg" % (urllib.quote(artist), urllib.quote(album)),
		"thumbnail_width": 600,
		"thumbnail_height": 600,
		"html": html,
		"width": width,
		"height": height,

		# oembed extension:
		"url": 'http://magnatune.com/artists/albums/%s/' % sku
	}

def query(params):
	action_name = params.getvalue('action')
	if action_name is None and 'url' in params:
		action_name = 'embed'
	elif action_name not in actions:
		raise AttributeError('Unknown action: %r' % action_name)

	conn = sqlite3.connect('sqlite_magnatune.db')
	try:
		body = actions[action_name](conn.cursor(),params)
	finally:
		conn.close()

	if action_name == 'embed':
		return body
	else:
		fp = open('changed.txt','r')
		try:
			changed = fp.read().strip()
		finally:
			fp.close()
		return {
			'head': {
				'version': '1.0',
				'changed': changed
			},
			'body': body
		}

params = cgi.FieldStorage()
response = query(params)
if 'callback' in params:
	sys.stdout.write(
		"Content-Type: text/javascript;charset=utf-8\r\n\r\n"+
		params.getvalue('callback')+'('+json.dumps(response)+')')
else:
	sys.stdout.write(
		"Content-Type: application/json;charset=utf-8\r\n\r\n"+
		json.dumps(response))

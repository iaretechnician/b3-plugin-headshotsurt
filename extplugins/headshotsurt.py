# headshotsurt Plugin for Big Brother Bot
# Copyright (C) 2008 Courgette
# Inspired by the spree plugin from Walker
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
__version__ = '1.2'
__author__  = 'Courgette'


from b3.plugin import Plugin
from b3.events import EVT_CLIENT_KILL, EVT_GAME_EXIT
from b3 import TEAM_BLUE, TEAM_RED, TEAM_UNKNOWN


class HeadShotsStats:
    headshots = 0
    kills = 0
    

class HeadshotsurtPlugin(Plugin):
    _adminPlugin = None
    _reset_headshots_stats = False
    _min_level_headshots_cmd = 0
    _clientvar_name = 'headshots_info'
    _show_awards = False

    def __init__(self, console, config=None):
        Plugin.__init__(self, console, config)
        if self.console.gameName not in ('iourt41', 'iourt42'):
            self.critical("unsupported game : %s" % self.console.gameName)
            raise SystemExit(220)

        ### kill modes constants ###
        try:
            self.UT_MOD_BLED = self.console.UT_MOD_BLED
        except AttributeError, err:
            self.warning("could not get UT_MOD_BLED value from B3 parser. %s" % err)
            self.UT_MOD_BLED = '23'
        self.debug("UT_MOD_BLED is %s" % self.UT_MOD_BLED)

        try:
            self.UT_MOD_HEGRENADE = self.console.UT_MOD_HEGRENADE
        except AttributeError, err:
            self.warning("could not get UT_MOD_HEGRENADE value from B3 parser. %s" % err)
            self.UT_MOD_HEGRENADE = '25'
        self.debug("UT_MOD_HEGRENADE is %s" % self.UT_MOD_HEGRENADE)

        ### hit location constants ###
        try:
            self.HL_HEAD = self.console.HL_HEAD
        except AttributeError, err:
            self.warning("could not get HL_HEAD value from B3 parser. %s" % err)
            if self.console.gameName == 'iourt41':
                self.HL_HEAD = '0'
            elif self.console.gameName == 'iourt42':
                self.HL_HEAD = '1'
        self.debug("HL_HEAD is %s" % self.HL_HEAD)

        try:
            self.HL_HELMET = self.console.HL_HELMET
        except AttributeError, err:
            self.warning("could not get HL_HELMET value from B3 parser. %s" % err)
            if self.console.gameName == 'iourt41':
                self.HL_HELMET = '1'
            elif self.console.gameName == 'iourt42':
                self.HL_HELMET = '2'
        self.debug("HL_HELMET is %s" % self.HL_HELMET)


    def onLoadConfig(self):

        try:
            self._reset_headshots_stats = self.config.getboolean('settings', 'reset_headshots')
        except Exception, err:
            self.warning("Using default value %s for reset_headshots. %s" % (self._reset_headshots_stats, err))
        self.debug('reset hs stats : %s' % self._reset_headshots_stats)
            
            
        try:
            self._show_awards = self.config.getboolean('settings', 'show_awards')
        except Exception, err:
            self.warning("Using default value %s for show_awards. %s" % (self._show_awards, err))
        self.debug('show awards : %s' % self._show_awards)
        
        
        try:
            self._min_level_headshots_cmd = self.config.getint('settings', 'min_level_headshots_cmd')
        except Exception, err:
            self.warning("Using default value %s for min_level_headshots_cmd. %s" % (self._min_level_headshots_cmd, err))
        self.debug('min level for hs cmd : %s' % self._min_level_headshots_cmd)
        

    def onStartup(self):
        self.registerEvent(EVT_CLIENT_KILL)
        self.registerEvent(EVT_GAME_EXIT)

        # get the plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
        else:
            self._adminPlugin.registerCommand(self, 'headshots', self._min_level_headshots_cmd, self.cmd_headshots, 'hs')



    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == EVT_CLIENT_KILL:
            self.handle_kills(event)
        elif event.type == EVT_GAME_EXIT:
            self.handle_gameexit(event)
              

    def init_headshots_stats(self, client):
        # initialize the clients spree stats
        client.setvar(self, self._clientvar_name, HeadShotsStats())


    def get_headshots_stats(self, client):
        
        if not client.isvar(self, self._clientvar_name):
            client.setvar(self, self._clientvar_name, HeadShotsStats())
            
        return client.var(self, self._clientvar_name).value


    def handle_kills(self, event):
        """\
        A kill was made. 
        """
        client = event.client
        if client:
            weapon = event.data[1]
            hitlocation = event.data[2]
            stats = self.get_headshots_stats(client)
            
            stats.kills += 1
            
            if weapon not in (self.UT_MOD_BLED, self.UT_MOD_HEGRENADE) and self.is_headshot(hitlocation):
                stats.headshots += 1
                self.show_message(client)
                

    def is_headshot(self, hitlocation):
        return hitlocation == self.HL_HEAD or hitlocation == self.HL_HELMET


    def show_message(self, client):
        """\
        display the message
        """
        s = self.get_headshots_stats(client)
        self.console.write('%s^3 made ^6%s^3 headshot%s' % (self.coloredClientName(client), s.headshots, 's' if s.headshots > 1 else ''))


    def cmd_headshots(self, data, client, cmd=None):
        """\
        [player] - Show a players number of headshots
        """        
        if data is None or data=='':
            if client is not None:
                s = self.get_headshots_stats(client)
                if s.headshots > 0:
                    cmd.sayLoudOrPM(client, '^7You made ^2%s^7 headshot%s' % (s.headshots, 's' if s.headshots > 1 else ''))
                else:
                    cmd.sayLoudOrPM(client, '^7You made no headshot')
        else:
            input = self._adminPlugin.parseUserCmd(data)
            if input:
                # input[0] is the player id
                sclient = self._adminPlugin.findClientPrompt(input[0], client)
                if not sclient:
                    # a player matchin the name was not found, a list of closest matches will be displayed
                    # we can exit here and the user will retry with a more specific player
                    return
            else:
                client.message('^7Invalid data, try !help headshots')
                return
            
            headshotsStats = self.get_headshots_stats(sclient)
            if headshotsStats.headshots > 0:
                client.message('^7%s made ^2%s^7 headshots' % (sclient.name, headshotsStats.headshots))
            else:
                client.message('^7%s made no headshot'%sclient.name)
       
       

    def handle_gameexit(self, event):
        if self._show_awards:
            maxHs = 0
            maxHsClients = []
            
            for c in self.console.clients.getList():
                stats = self.get_headshots_stats(c)
                # self.debug("[%s] HS:%s K:%s" % (c.name, stats.headshots, stats.kills))
                
                if stats.headshots > maxHs:
                    maxHs = stats.headshots
                    ratio = None
                    if stats.kills > 0:
                        ratio = float(stats.headshots) / stats.kills
                    maxHsClients = [(c, ratio)]
                elif stats.headshots>0 and stats.headshots == maxHs:
                    ratio = None
                    if stats.kills > 0:
                        ratio = float(stats.headshots) / stats.kills
                    maxHsClients.append((c, ratio))
                    
                if stats.kills > 0:
                    ratio = float(stats.headshots) / stats.kills
                    self.debug("[%s] HS:%s K:%s => ratio %.2f" % (c.name, stats.headshots, stats.kills, ratio))
        
            
            for c, ratio in maxHsClients:
                #self.debug("Most HS found : %s (%s)" % (c.name, maxHs))
                self.console.say('^2Most HS Award : %s^3 (^6%s^3 HS, ratio: %.2f)'%(self.coloredClientName(c), maxHs, ratio))

                
        if self._reset_headshots_stats:
            for c in self.console.clients.getList():
                self.init_headshots_stats(c)
                
                
                
    def coloredClientName(self, client):
        # color name with team color
        clientName = client.name
        if client.team == TEAM_RED:
            clientName = '^1%s^7' % client.name
        elif client.team == TEAM_BLUE:
            clientName = '^4%s^7' % client.name
        elif client.team == TEAM_UNKNOWN:
            clientName = '^3%s^7' % client.name
        return clientName
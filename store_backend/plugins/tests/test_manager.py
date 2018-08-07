
import time
import json

from django.contrib.auth.models import User
from django.test import TestCase, tag

from plugins.models import Plugin, PluginParameter
from plugins.services import manager


class PluginManagerTests(TestCase):

    def setUp(self):
        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.plugin_parameters = [
            {'name': 'dir', 'type': str.__name__, 'action': 'store',
             'optional': False, 'flag': '--dir', 'default': '',
             'help': 'test plugin'}]
        self.plg_repr = {}
        self.plg_repr['type'] = 'fs'
        self.plg_repr['icon'] = 'http://github.com/plugin'
        self.plg_repr['authors'] = 'DEV FNNDSC'
        self.plg_repr['title'] = 'Dir plugin'
        self.plg_repr['category'] = 'Dir'
        self.plg_repr['description'] = 'Dir test plugin'
        self.plg_repr['license'] = 'MIT'
        self.plg_repr['version'] = 'v0.1'
        self.plg_repr['execshell'] = 'python3'
        self.plg_repr['selfpath'] = '/usr/src/simplefsapp'
        self.plg_repr['selfexec'] = 'simplefsapp.py'
        self.plg_repr['parameters'] = self.plugin_parameters

        user = User.objects.create_user(username=self.username, email=self.email,
                                        password=self.password)

        # create a plugin
        data = self.plg_repr.copy()
        del data['parameters']
        data['name'] = self.plugin_name
        (plugin, tf) = Plugin.objects.get_or_create(**data)
        plugin.owner.set([user])

        # add plugin's parameters
        parameters = self.plugin_parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=parameters[0]['name'],
            type=parameters[0]['type'],
            flag=parameters[0]['flag'])

        self.pl_manager = manager.PluginManager()


    def test_mananger_can_get_plugin(self):
        """
        Test whether the manager can return a plugin object.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        self.assertEquals(plugin, self.pl_manager.get_plugin(self.plugin_name))

    def test_mananger_can_add_plugin(self):
        """
        Test whether the manager can add a new plugin to the system.
        """
        self.pl_manager.run(['add', 'testapp', self.username, 'http://github.com/repo',
                             'fnndsc/pl-testapp', '--descriptorstring',
                             json.dumps(self.plg_repr)])
        self.assertEquals(Plugin.objects.count(), 2)
        self.assertTrue(PluginParameter.objects.count() > 1)

    def test_mananger_can_modify_plugin(self):
        """
        Test whether the manager can modify an existing plugin.
        """
        # create another chris store user
        user = User.objects.create_user(username='another', email='another@babymri.org',
                                 password='anotherpassword')
        self.plg_repr['selfexec'] = 'testapp.py'
        plugin = Plugin.objects.get(name=self.plugin_name)
        initial_modification_date = plugin.modification_date
        time.sleep(1)
        self.pl_manager.run(['modify', self.plugin_name, 'http://github.com/repo',
                             'fnndsc/pl-testapp', '--newowner', user.username,
                             '--descriptorstring', json.dumps(self.plg_repr)])

        plugin = Plugin.objects.get(name=self.plugin_name)
        self.assertTrue(plugin.modification_date > initial_modification_date)
        self.assertEquals(plugin.selfexec,'testapp.py')
        user1 = User.objects.get(username=self.username)
        self.assertCountEqual(plugin.owner.all(), [user1, user])

    def test_mananger_can_remove_plugin(self):
        """
        Test whether the manager can remove an existing plugin from the system.
        """
        self.pl_manager.run(['remove', self.plugin_name])
        self.assertEquals(Plugin.objects.count(), 0)
        self.assertEquals(PluginParameter.objects.count(), 0)

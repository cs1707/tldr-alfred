# -*- coding: utf_8 -*-
# author www.chedanji.com

from xml.etree import ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, ElementTree
import subprocess
from xml.dom import minidom
import os
import time
import io
import json
import getopt
import datetime

alfred_workflow_data = os.environ['alfred_workflow_data']
repo_directory = alfred_workflow_data + '/tldr'
default_platform = 'osx'

def query(query):
  global default_platform
  clone()

  dic = parse_args(query)
  isUpdate = dic['isUpdate']
  default_platform = dic['platform']
  command = dic['command']

  if bool(isUpdate):
    update()
    outputTitle('Update success')
  else:
    update(7)

  if(len(query) == 0):
    rowList = [{
      'uid': '1',
      'arg': '',
      'autocomplete': '',
      'icon': 'icon.png',
      'title': 'Please input',
      'valid': 'no'
    }]
  else:
    rowList = parse_man_page(command)
    if(len(rowList) == 0):
      rowList = [{
        'uid': '1',
        'arg': '',
        'autocomplete': '',
        'icon': 'icon.png',
        'title': 'Page not found',
        'valid': 'no'
      }]
  print genXML(rowList)

def find_page_location(command):

  with io.open(os.path.join(repo_directory, 'pages/index.json'),
               encoding='utf-8') as f:
    index = json.load(f)
  command_list = [item['name'] for item in index['commands']]
  if command not in command_list:
    return

  supported_platforms = index['commands'][
    command_list.index(command)]['platform']
  if default_platform in supported_platforms:
    platform = default_platform
  elif 'common' in supported_platforms:
    platform = 'common'
  else:
    platform = ''

  if not platform:
    return
  page_path = os.path.join(os.path.join(repo_directory, 'pages'),
                        os.path.join(platform, command + '.md'))
  return page_path

def parse_page(page):
  with io.open(page, encoding='utf-8') as f:
    lines = f.readlines()
  rowList = []
  uid = 1
  item = {}
  description = {}
  for line in lines:
    if line.startswith('#'):
      continue
    elif line.startswith('>'):
      description['title'] = line.replace('>', '').strip()
      description['uid'] = str(uid)
    elif line.startswith('-'):
      item = {}
      item['uid'] = str(uid)
      item['subtitle'] = line.replace('-', '').strip()
    elif line.startswith('`'):
      item['title'] = line.replace('`', '').replace('{{', '').replace('}}', '').replace(' ', '  ').strip()
      rowList.append(item)

    uid += 1
  rowList.insert(0, description)
  return rowList

def parse_man_page(command):
  page_path = find_page_location(command)
  if page_path:
    return parse_page(page_path)

  return []

def genXML(rowList):
  items = Element('items')

  for row in rowList:
    item = SubElement(items, 'item')
    item.set('autocomplete', row.get('title') or '')
    item.set('uid', row.get('uid') or '')
    item.set('arg', row.get('title') or '')
    item.set('valid', row.get('valid') or '')

    title = SubElement(item, 'title')
    title.text = row.get('title') or ''

    subtitle = SubElement(item, 'subtitle')
    subtitle.text = row.get('subtitle') or ''

    icon = SubElement(item, 'icon')
    icon.text = row.get('icon')

  tree = minidom.parseString(etree.tostring(items))
  return tree.toxml()

def outputTitle(msg):
  print genXML([{
        'uid': str(time.time()),
        'arg': '',
        'autocomplete': '',
        'icon': 'icon.png',
        'title': str(msg),
        'valid': 'no'
      }])

def clone():
  if(not os.path.exists(alfred_workflow_data)):
    os.mkdir(alfred_workflow_data)

  if(not os.path.exists(repo_directory)):
    child = subprocess.Popen(['git clone https://github.com/tldr-pages/tldr.git ' + '"' + str(repo_directory) + '"'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    success, err = child.communicate()

def update(days=0):

  if days > 0 and os.path.exists(os.path.join(alfred_workflow_data, 'config.json')):
    with io.open(os.path.join(alfred_workflow_data, 'config.json'),
        encoding='utf-8') as f:
      try:
        config = json.load(f)
      except:
        config = {'update_date': datetime.datetime.now().strftime('%Y%m%d')}

    if (datetime.datetime.now().date() - datetime.datetime.strptime(config['update_date'], '%Y%m%d').date()).days < days:
      return
  os.chdir(repo_directory)
  local = subprocess.check_output('git rev-parse master'.split()).strip()
  remote = subprocess.check_output(
    'git ls-remote https://github.com/tldr-pages/tldr/ HEAD'.split()
  ).split()[0]

  if local != remote:
    subprocess.check_call('git checkout master'.split())
    subprocess.check_call('git pull --rebase'.split())

  with io.open(os.path.join(alfred_workflow_data, 'config.json'), mode='wb') as f:
    data = {
      'update_date': datetime.datetime.now().strftime('%Y%m%d')
    }
    json.dump(data, f)

def parse_args(query=''):
  query = query.split()
  dic = {
    'isUpdate': False,
    'platform': default_platform,
    'command': ''
  }
  try:
    opts, args = getopt.gnu_getopt(query, 'uo:')
  except:
    return dic

  for opt, arg in opts:
    if opt == '-u':
      dic['isUpdate'] = True
    elif opt == '-o':
      dic['platform'] = arg

  dic['command'] = '-'.join(args)

  return dic

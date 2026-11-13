import re

def strip_shadow_fields(text):
 return '\n'.join(line for line in text.splitlines() if line.strip() not in ('- _SHADOW_NORMAL_BIAS_SCALE','- _ShadowNormalBiasScale: 0','- _ShadowNormalBiasScale: 1'))+'\n'

def normalize_invalid(text, baseline, name):
 pattern=r'(?m)^  m_InvalidKeywords:.*\n(?:  - [^\n]*\n)*'
 old=re.search(pattern,baseline).group();new=re.search(pattern,text).group()
 old_keys=set(re.findall(r'^  - (.+)$',old,re.M));new_keys=set(re.findall(r'^  - (.+)$',new,re.M))
 assert old_keys<=new_keys and new_keys-old_keys<={'_RECEIVESHADOWS_ON','_ZWRITE_ON'}, 'Unexpected invalid-keyword change: '+name
 return text.replace(new,old,1)

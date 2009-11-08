from django.db import models
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson

# JSONField is from Djblets
# (http://code.google.com/p/reviewboard/wiki/Djblets), which is by
# Christian Hammond and David Trowbridge.
class JSONField(models.TextField):
    """
    A field for storing JSON-encoded data. The data is accessible as standard
    Python data types and is transparently encoded/decoded to/from a JSON
    string in the database.
    """
    serialize_to_string = True

    def __init__(self, verbose_name=None, name=None,
                 encoder=DjangoJSONEncoder(), **kwargs):
        models.TextField.__init__(self, verbose_name, name, blank=True,
                                  **kwargs)
        self.encoder = encoder

    def db_type(self):
        return "text"

    def contribute_to_class(self, cls, name):
        def get_json(model_instance):
            return self.dumps(getattr(model_instance, self.attname, None))

        def set_json(model_instance, json):
            setattr(model_instance, self.attname, self.loads(json))

        super(JSONField, self).contribute_to_class(cls, name)

        setattr(cls, "get_%s_json" % self.name, get_json)
        setattr(cls, "set_%s_json" % self.name, set_json)

        models.signals.post_init.connect(self.post_init, sender=cls)

    def pre_save(self, model_instance, add):
        return self.dumps(getattr(model_instance, self.attname, None))

    def post_init(self, instance=None, **kwargs):
        value = self.value_from_object(instance)

        if value:
            try:
                value = self.loads(value)
            except (ValueError, SyntaxError):
                #Was getting "''", and breaking
                pass
        else:
            value = {}

        setattr(instance, self.attname, value)

    def get_db_prep_save(self, value):
        if not isinstance(value, basestring):
            value = self.dumps(value)

        return super(JSONField, self).get_db_prep_save(value)

    def value_to_string(self, obj):
        return self.dumps(self.value_from_object(obj))

    def dumps(self, data):
        return self.encoder.encode(data)

    def loads(self, val):
        try:
            val = simplejson.loads(val, encoding=settings.DEFAULT_CHARSET)

            # XXX We need to investigate why this is happening once we have
            #     a solid repro case.
            if isinstance(val, basestring):
                # logging.warning("JSONField decode error. Expected dictionary, "
                #                 "got string for input '%s'" % val)
                # For whatever reason, we may have gotten back
                val = simplejson.loads(val, encoding=settings.DEFAULT_CHARSET)
        except ValueError:
            # There's probably embedded unicode markers (like u'foo') in the
            # string. We have to eval it.
            val = eval(val)

        return val

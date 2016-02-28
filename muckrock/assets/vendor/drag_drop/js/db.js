var levelup = require('levelup');
var leveljs = require('level-js');
var db = levelup('bitvoyage', { db: leveljs });

var Session = {

  db: db,

  put: function(key, obj, cb) {
    if (!cb) cb = function() {};

    db.put(key, JSON.stringify(obj), cb);
  },

  get: function(key, cb) {
    if (!cb) cb = function() {};

    db.get(key, function(err, data) {
      if (err) return cb(err);

      cb(null, JSON.parse(data));
    })
  },

  // uploads: function() {

  // }

  servers: function(cb) {
    if (!cb) cb = function() {};

    db.get("servers", function(err, value) {
      if (err) return cb(null, {});

      cb(null, JSON.parse(value))
    })
  },

    addServer: function(id, details, cb) {
      if (!cb) cb = function() {};

      Session.servers(function(err, servers) {
        if (err) return cb(err);

        servers[id] = details;
        console.log(JSON.stringify(servers));
        db.put("servers", JSON.stringify(servers), function(err) {
          if (err) return cb(err);

          if (cb) Session.servers(cb);
        });
      });
    },

    removeServer: function(id, cb) {
      if (!cb) cb = function() {};

      Session.servers(function(err, servers) {
        if (err) return cb(err);

        delete servers[id];
        db.put("servers", JSON.stringify(servers), cb);
      });
    },

    clearServers: function(cb) {
      db.del("servers", cb);
    }

};

module.exports = Session;

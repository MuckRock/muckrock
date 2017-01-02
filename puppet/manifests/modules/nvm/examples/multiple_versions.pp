class { 'nvm':
  user => 'foo',
  node_instances => {
    '0.12.7'  => {
      set_default => true,
    },
    '0.10.36' => {},
    'iojs'    => {},
  }
}

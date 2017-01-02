class { 'nvm':
  user => 'foo',
} ->

nvm::node::install { '0.12.7':
  user        => 'foo',
  set_default => true,
} ->

nvm::node::install { '0.10.36':
  user => 'foo',
} ->

nvm::node::install { 'iojs':
  user => 'foo',
}

# -*- mode: ruby -*-
# vi: set ft=ruby :

VERSION = "2" # Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
BOX = "bento/ubuntu-16.04"
PORT = 8000
CPUS = ENV.fetch('CPUS', 2)
MEMORY = ENV.fetch('MEMORY', 2048)

Vagrant.configure(VERSION) do |config|
  config.vm.box = BOX
  config.vm.network :private_network, type: :dhcp
  config.vm.network :forwarded_port, guest: PORT, host: PORT, auto_correct: true
  config.vm.synced_folder ".", "/home/vagrant/muckrock/"

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--ioapic", "on"]
    v.customize ["modifyvm", :id, "--cpuexecutioncap", "90"]
    v.customize ["modifyvm", :id, "--cpus", CPUS]
    v.customize ["modifyvm", :id, "--memory", MEMORY]
  end

  config.vm.provision :shell, inline: "sudo apt --assume-yes install puppet"
  # provision with puppet
  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet/manifests"
    puppet.manifest_file = "default.pp"
    puppet.module_path = "puppet/manifests/modules"
  end

end

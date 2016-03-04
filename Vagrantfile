# -*- mode: ruby -*-
# vi: set ft=ruby :

VERSION = "2" # Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
BOX = "ubuntu/wily64"
BOX_URL = "https://vagrantcloud.com/ubuntu/boxes/wily64/versions/20160226.0.0/providers/virtualbox.box"
PORT = 8000

Vagrant.configure(VERSION) do |config|
  config.vm.box = BOX
  config.vm.box_url = BOX_URL
  config.vm.network :private_network, type: :dhcp
  config.vm.network :forwarded_port, guest: PORT, host: PORT
  config.vm.synced_folder ".", "/home/vagrant/muckrock/",
	  :nfs => true,
	  :mount_options => ['nolock,vers=3,udp,noatime,actimeo=1']

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--ioapic", "on"]
    v.customize ["modifyvm", :id, "--cpuexecutioncap", "90"]
    v.customize ["modifyvm", :id, "--cpus", 4]
    v.customize ["modifyvm", :id, "--memory", 2048]
  end

  # provision with puppet
  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet/manifests"
    puppet.manifest_file = "default.pp"
    puppet.module_path = "puppet/manifests/modules"
  end

end

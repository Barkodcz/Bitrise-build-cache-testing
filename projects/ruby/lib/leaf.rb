# Nothing depends on this module -- tools/simulate-change.sh ruby leaf mutates label() here for the
# "leaf" change kind (spec §4.1 default).
module Leaf
  def self.label
    "leaf-v1"
  end
end

from util.block_utils import getBlockAlignment

def assignAlignToBlocks(blocks):
    for block in blocks:
        alignment = getBlockAlignment(block)
        block["align"] = alignment

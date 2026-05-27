define i32 @chain_lshr_shl_8_8(i32 %x) {
entry:
  %tmp = lshr i32 %x, 8
  %result = shl i32 %tmp, 8
  ret i32 %result
}

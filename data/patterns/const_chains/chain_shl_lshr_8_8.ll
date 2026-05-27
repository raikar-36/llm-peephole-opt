define i32 @chain_shl_lshr_8_8(i32 %x) {
entry:
  %tmp = shl i32 %x, 8
  %result = lshr i32 %tmp, 8
  ret i32 %result
}

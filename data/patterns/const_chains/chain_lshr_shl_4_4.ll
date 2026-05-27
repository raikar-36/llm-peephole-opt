define i32 @chain_lshr_shl_4_4(i32 %x) {
entry:
  %tmp = lshr i32 %x, 4
  %result = shl i32 %tmp, 4
  ret i32 %result
}

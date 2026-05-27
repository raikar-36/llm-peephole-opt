define i32 @chain_shl_lshr_4_4(i32 %x) {
entry:
  %tmp = shl i32 %x, 4
  %result = lshr i32 %tmp, 4
  ret i32 %result
}

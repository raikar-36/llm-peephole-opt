define i32 @chain_shl_lshr_2_2(i32 %x) {
entry:
  %tmp = shl i32 %x, 2
  %result = lshr i32 %tmp, 2
  ret i32 %result
}

define i32 @chain_lshr_shl_2_2(i32 %x) {
entry:
  %tmp = lshr i32 %x, 2
  %result = shl i32 %tmp, 2
  ret i32 %result
}
